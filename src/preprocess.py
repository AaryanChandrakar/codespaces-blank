"""
Data preprocessing module for augmentation and train/val/test splitting.
Converts raw images to YOLO-format directory structure.
"""
import logging
import shutil
import random
from pathlib import Path
from typing import Dict, Tuple, List
import numpy as np
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2

from src.config_loader import load_config

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocess raw images: augment, validate, and split into train/val/test."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize preprocessor with configuration.
        
        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = load_config(config_path)
        self.raw_dir = Path(self.config["project"]["raw_dir"])
        self.processed_dir = Path(self.config["project"]["processed_dir"])
        self.classes = self.config.get("classes", [])
        
        self.preprocess_config = self.config.get("preprocessing", {})
        self.train_split = self.preprocess_config.get("train_split", 0.8)
        self.val_split = self.preprocess_config.get("val_split", 0.1)
        self.test_split = self.preprocess_config.get("test_split", 0.1)
        self.seed = self.preprocess_config.get("seed", 42)
        self.aug_enabled = self.preprocess_config.get("augmentation", {}).get("enabled", False)
        self.aug_factor = self.preprocess_config.get("augmentation", {}).get("augmentation_factor", 1)
        
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        # Create YOLO directory structure
        self._create_yolo_structure()
    
    def _create_yolo_structure(self) -> None:
        """Create YOLO-format directory structure."""
        for split in ["train", "val", "test"]:
            (self.processed_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (self.processed_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
        logger.info("Created YOLO directory structure")
    
    def _get_augmentation_transform(self) -> A.Compose:
        """
        Create Albumentations augmentation pipeline.
        
        Returns:
            Albumentations Compose object with augmentations.
        """
        aug_config = self.preprocess_config.get("augmentation", {}).get("transforms", {})
        
        transforms = []
        
        if aug_config.get("horizontal_flip"):
            transforms.append(A.HorizontalFlip(p=aug_config["horizontal_flip"]))
        
        if aug_config.get("vertical_flip"):
            transforms.append(A.VerticalFlip(p=aug_config["vertical_flip"]))
        
        if aug_config.get("rotation"):
            transforms.append(A.Rotate(limit=aug_config["rotation"], p=0.5))
        
        if aug_config.get("brightness"):
            transforms.append(A.RandomBrightnessContrast(
                brightness_limit=aug_config["brightness"],
                contrast_limit=0,
                p=0.5
            ))
        
        if aug_config.get("contrast"):
            transforms.append(A.RandomBrightnessContrast(
                brightness_limit=0,
                contrast_limit=aug_config["contrast"],
                p=0.5
            ))
        
        if aug_config.get("blur"):
            transforms.append(A.GaussBlur(blur_limit=aug_config["blur"], p=0.3))
        
        return A.Compose(transforms, bbox_params=A.BboxParams(format='pascal_voc', min_visibility=0.3))
    
    def _augment_image(self, image_path: str, class_id: int, output_dir: Path, count: int) -> List[str]:
        """
        Augment a single image using Albumentations.
        
        Args:
            image_path: Path to input image.
            class_id: Class ID for YOLO label.
            output_dir: Directory to save augmented images.
            count: Number of augmentations to create.
        
        Returns:
            List of output image filenames (without bboxes, just images).
        """
        try:
            image = Image.open(image_path).convert("RGB")
            image_array = np.array(image)
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return []
        
        augment_transform = self._get_augmentation_transform()
        output_files = []
        
        for i in range(count):
            try:
                # Apply augmentation (without bboxes for simplicity)
                augmented = augment_transform(image=image_array)
                aug_image = Image.fromarray(augmented["image"].astype("uint8"))
                
                # Save augmented image
                base_name = Path(image_path).stem
                output_file = output_dir / f"{base_name}_aug_{i}.jpg"
                aug_image.save(output_file, "JPEG", quality=95)
                
                # Create corresponding label file (single class, full image)
                label_file = output_dir.parent / "labels" / output_file.stem
                with open(f"{label_file}.txt", "w") as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
                
                output_files.append(str(output_file))
            except Exception as e:
                logger.error(f"Error augmenting {image_path} (iteration {i}): {e}")
        
        return output_files
    
    def preprocess_and_split(self) -> Dict[str, int]:
        """
        Preprocess images: augment, validate, and split into train/val/test.
        
        Returns:
            Dictionary with split statistics.
        """
        all_images = []
        image_to_class = {}
        
        # Collect all images and their class IDs
        for class_id, class_name in enumerate(self.classes):
            class_dir = self.raw_dir / class_name
            if not class_dir.exists():
                logger.warning(f"Class directory not found: {class_dir}")
                continue
            
            for img_file in class_dir.glob("*"):
                if img_file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    all_images.append(str(img_file))
                    image_to_class[str(img_file)] = class_id
        
        if not all_images:
            logger.error("No images found in raw directory")
            return {}
        
        logger.info(f"Found {len(all_images)} images across {len(self.classes)} classes")
        
        # Shuffle and split
        random.shuffle(all_images)
        train_count = int(len(all_images) * self.train_split)
        val_count = int(len(all_images) * self.val_split)
        
        train_images = all_images[:train_count]
        val_images = all_images[train_count:train_count + val_count]
        test_images = all_images[train_count + val_count:]
        
        splits = {
            "train": (train_images, self.processed_dir / "images" / "train"),
            "val": (val_images, self.processed_dir / "images" / "val"),
            "test": (test_images, self.processed_dir / "images" / "test"),
        }
        
        stats = {}
        
        for split_name, (images, output_dir) in splits.items():
            logger.info(f"Processing {split_name} split ({len(images)} images)...")
            
            aug_count = self.aug_factor if split_name == "train" else 1
            
            for img_path in images:
                class_id = image_to_class[img_path]
                
                try:
                    # Copy original image
                    img = Image.open(img_path).convert("RGB")
                    base_name = Path(img_path).stem
                    output_img = output_dir / f"{base_name}.jpg"
                    img.save(output_img, "JPEG", quality=95)
                    
                    # Create label file
                    label_file = output_dir.parent / "labels" / output_img.stem
                    with open(f"{label_file}.txt", "w") as f:
                        f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
                    
                    # Augment if enabled and in training set
                    if self.aug_enabled and split_name == "train" and aug_count > 1:
                        self._augment_image(img_path, class_id, output_dir, aug_count - 1)
                
                except Exception as e:
                    logger.error(f"Error processing {img_path}: {e}")
            
            stats[split_name] = len(list(output_dir.glob("*.jpg")))
            logger.info(f"  Completed {split_name}: {stats[split_name]} images")
        
        return stats
    
    def get_dataset_yaml(self) -> str:
        """
        Generate YOLO dataset.yaml content.
        
        Returns:
            YAML string for YOLO training.
        """
        nc = len(self.classes)
        names = {i: name for i, name in enumerate(self.classes)}
        
        yaml_content = f"""path: {str(self.processed_dir)}
train: images/train
val: images/val
test: images/test

nc: {nc}
names: {names}
"""
        return yaml_content
    
    def save_dataset_yaml(self, output_path: str = "data.yaml") -> None:
        """
        Save YOLO dataset.yaml to file.
        
        Args:
            output_path: Path to save the YAML file.
        """
        yaml_content = self.get_dataset_yaml()
        with open(output_path, "w") as f:
            f.write(yaml_content)
        logger.info(f"Saved dataset.yaml to {output_path}")


def main(config_path: str = "config/config.yaml"):
    """
    Main entry point for preprocessing.
    
    Args:
        config_path: Path to configuration YAML file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    preprocessor = DataPreprocessor(config_path)
    stats = preprocessor.preprocess_and_split()
    preprocessor.save_dataset_yaml("data.yaml")
    
    logger.info("="*50)
    logger.info("Preprocessing Summary:")
    for split, count in stats.items():
        logger.info(f"  {split}: {count} images")
    logger.info("="*50)


if __name__ == "__main__":
    main()
