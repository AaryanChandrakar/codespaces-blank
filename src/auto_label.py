"""
Auto-labeling module for generating initial YOLO labels using pre-trained YOLOv8n.
These labels should be reviewed and corrected manually using annotation tools like LabelImg.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    logging.error("ultralytics not installed. Install with: pip install ultralytics")
    raise

from src.config_loader import load_config

logger = logging.getLogger(__name__)


class AutoLabeler:
    """Generate initial YOLO labels using pre-trained YOLOv8n model."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize auto-labeler with configuration.
        
        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = load_config(config_path)
        self.raw_dir = Path(self.config["project"]["raw_dir"])
        self.classes = self.config.get("classes", [])
        
        self.auto_label_config = self.config.get("auto_label", {})
        self.model_name = self.auto_label_config.get("model_name", "yolov8n")
        self.conf_threshold = self.auto_label_config.get("confidence_threshold", 0.3)
        self.iou_threshold = self.auto_label_config.get("iou_threshold", 0.45)
        
        logger.info(f"Loading pre-trained {self.model_name} model (will download if needed)...")
        # Pass the model name (e.g. 'yolov8n') to let ultralytics handle download/resolution
        self.model = YOLO(self.model_name)
    
    def _normalize_bbox(self, bbox: Tuple[float, float, float, float], 
                       img_width: int, img_height: int) -> Tuple[float, float, float, float]:
        """
        Convert bbox from absolute coordinates to YOLO normalized format (0-1).
        
        Args:
            bbox: Bounding box as (x1, y1, x2, y2) in absolute coordinates.
            img_width: Image width in pixels.
            img_height: Image height in pixels.
        
        Returns:
            Normalized bbox as (center_x, center_y, width, height) in range [0, 1].
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / (2 * img_width)
        center_y = (y1 + y2) / (2 * img_height)
        width = (x2 - x1) / img_width
        height = (y2 - y1) / img_height
        
        return center_x, center_y, width, height
    
    def _find_closest_class(self, detection_name: str) -> int:
        """
        Map COCO detection class name to project class ID.
        Uses simple heuristic matching.
        
        Args:
            detection_name: Class name from model detection.
        
        Returns:
            Class ID from project classes, or -1 if no match.
        """
        detection_lower = detection_name.lower()
        
        for class_id, class_name in enumerate(self.classes):
            if any(keyword in detection_lower for keyword in class_name.split("_")):
                return class_id
        
        # Default heuristic for plastic detection
        if "bottle" in detection_lower:
            return self.classes.index("plastic_bottle") if "plastic_bottle" in self.classes else -1
        elif "bag" in detection_lower:
            return self.classes.index("plastic_bag") if "plastic_bag" in self.classes else -1
        elif "plastic" in detection_lower or "wrapper" in detection_lower:
            return self.classes.index("plastic_wrapper") if "plastic_wrapper" in self.classes else -1
        
        return -1
    
    def auto_label_directory(self, class_dir: Path) -> Tuple[int, int]:
        """
        Auto-label all images in a class directory.
        
        Args:
            class_dir: Directory containing raw images for a class.
        
        Returns:
            Tuple of (total_images, labeled_images).
        """
        labeled_count = 0
        total_count = 0
        
        logger.info(f"Auto-labeling {class_dir.name}...")
        
        for img_file in sorted(class_dir.glob("*")):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue
            
            total_count += 1
            
            try:
                # Run inference
                results = self.model(str(img_file), conf=self.conf_threshold, iou=self.iou_threshold)
                
                # Load image to get dimensions
                img = cv2.imread(str(img_file))
                if img is None:
                    logger.warning(f"Failed to read image: {img_file}")
                    continue
                
                height, width = img.shape[:2]
                
                # Extract detections
                label_lines = []
                if len(results) > 0 and results[0].boxes is not None:
                    for box in results[0].boxes:
                        conf = float(box.conf[0])
                        class_id_coco = int(box.cls[0])
                        class_name_coco = self.model.names[class_id_coco]
                        
                        # Map to project class
                        project_class_id = self._find_closest_class(class_name_coco)
                        
                        if project_class_id >= 0:
                            bbox = tuple(map(float, box.xyxy[0]))
                            norm_bbox = self._normalize_bbox(bbox, width, height)
                            label_lines.append(f"{project_class_id} {norm_bbox[0]:.6f} {norm_bbox[1]:.6f} {norm_bbox[2]:.6f} {norm_bbox[3]:.6f}")
                
                # If no detections, create empty label or default label
                if not label_lines:
                    # Create empty label file
                    label_file = img_file.with_suffix(".txt")
                    label_file.write_text("")
                    logger.debug(f"No detections in {img_file.name}")
                else:
                    # Save label file
                    label_file = img_file.with_suffix(".txt")
                    label_file.write_text("\n".join(label_lines) + "\n")
                    labeled_count += 1
                    logger.debug(f"Labeled {img_file.name} with {len(label_lines)} detections")
            
            except Exception as e:
                logger.error(f"Error processing {img_file}: {e}")
        
        return total_count, labeled_count
    
    def auto_label_all(self) -> Dict[str, Tuple[int, int]]:
        """
        Auto-label all images in raw directory.
        
        Returns:
            Dictionary with class names and (total, labeled) counts.
        """
        results = {}
        
        for class_name in self.classes:
            class_dir = self.raw_dir / class_name
            if class_dir.exists():
                total, labeled = self.auto_label_directory(class_dir)
                results[class_name] = (total, labeled)
            else:
                logger.warning(f"Class directory not found: {class_dir}")
                results[class_name] = (0, 0)
        
        return results


def main(config_path: str = "config/config.yaml"):
    """
    Main entry point for auto-labeling.
    
    Args:
        config_path: Path to configuration YAML file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    labeler = AutoLabeler(config_path)
    results = labeler.auto_label_all()
    
    logger.info("="*50)
    logger.info("Auto-Labeling Summary:")
    total_images = 0
    total_labeled = 0
    for class_name, (total, labeled) in results.items():
        logger.info(f"  {class_name}: {labeled}/{total} labeled")
        total_images += total
        total_labeled += labeled
    logger.info(f"Total: {total_labeled}/{total_images} images labeled")
    logger.info("="*50)
    logger.info("Note: Review and correct labels manually using LabelImg or similar tool.")


if __name__ == "__main__":
    main()
