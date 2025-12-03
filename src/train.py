"""
Training module for YOLOv8 model on plastic waste detection dataset.
"""
import logging
from pathlib import Path
from typing import Dict, Any

try:
    from ultralytics import YOLO
except ImportError:
    logging.error("ultralytics not installed. Install with: pip install ultralytics")
    raise

from src.config_loader import load_config

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train YOLOv8 model on plastic waste detection dataset."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize trainer with configuration.
        
        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = load_config(config_path)
        self.models_dir = Path(self.config["project"]["models_dir"])
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.train_config = self.config.get("training", {})
        self.model_name = self.train_config.get("model_name", "yolov8m")
        self.epochs = self.train_config.get("epochs", 50)
        self.batch_size = self.train_config.get("batch_size", 16)
        self.img_size = self.train_config.get("img_size", 640)
        self.patience = self.train_config.get("patience", 10)
        self.device = self.train_config.get("device", 0)
        self.optimizer = self.train_config.get("optimizer", "SGD")
        self.lr = self.train_config.get("learning_rate", 0.01)
        self.weight_decay = self.train_config.get("weight_decay", 0.0005)
        self.momentum = self.train_config.get("momentum", 0.937)
        self.seed = self.train_config.get("seed", 42)
        
        logger.info(f"Initializing {self.model_name} model (will download if needed)...")
        # Pass the model name (e.g. 'yolov8m') so ultralytics can resolve/download the weights
        self.model = YOLO(self.model_name)
    
    def train(self, data_yaml: str = "data.yaml") -> Dict[str, Any]:
        """
        Train the YOLOv8 model.
        
        Args:
            data_yaml: Path to YOLO dataset.yaml file.
        
        Returns:
            Training results dictionary.
        """
        if not Path(data_yaml).exists():
            raise FileNotFoundError(f"Dataset YAML not found: {data_yaml}")
        
        logger.info(f"Starting training with {self.model_name}...")
        logger.info(f"  Dataset: {data_yaml}")
        logger.info(f"  Epochs: {self.epochs}, Batch Size: {self.batch_size}")
        logger.info(f"  Image Size: {self.img_size}, Device: {self.device}")
        
        try:
            results = self.model.train(
                data=data_yaml,
                epochs=self.epochs,
                imgsz=self.img_size,
                batch=self.batch_size,
                patience=self.patience,
                device=self.device,
                optimizer=self.optimizer,
                lr0=self.lr,
                weight_decay=self.weight_decay,
                momentum=self.momentum,
                seed=self.seed,
                project="runs/detect",
                name="plastic_detection",
                exist_ok=True,
                save=True,
                save_period=10,
                cache=False,
                verbose=True,
            )
            
            logger.info("Training completed successfully!")
            
            # Copy best model to models directory
            best_model_path = Path("runs/detect/plastic_detection/weights/best.pt")
            if best_model_path.exists():
                import shutil
                dst_path = self.models_dir / "best.pt"
                shutil.copy2(best_model_path, dst_path)
                logger.info(f"Best model saved to: {dst_path}")
            
            return {"status": "success", "results": results}
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def validate(self, model_path: str = None) -> Dict[str, Any]:
        """
        Validate model on validation set.
        
        Args:
            model_path: Path to trained model. If None, uses best.pt from models_dir.
        
        Returns:
            Validation results.
        """
        if model_path is None:
            model_path = str(self.models_dir / "best.pt")
        
        if not Path(model_path).exists():
            logger.error(f"Model not found: {model_path}")
            return {"status": "failed", "error": "Model not found"}
        
        logger.info(f"Validating model: {model_path}")
        
        try:
            model = YOLO(model_path)
            metrics = model.val()
            logger.info("Validation completed!")
            return {"status": "success", "metrics": metrics}
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"status": "failed", "error": str(e)}


def main(config_path: str = "config/config.yaml", data_yaml: str = "data.yaml"):
    """
    Main entry point for training.
    
    Args:
        config_path: Path to configuration YAML file.
        data_yaml: Path to dataset.yaml file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    trainer = ModelTrainer(config_path)
    result = trainer.train(data_yaml)
    
    logger.info("="*50)
    logger.info("Training Summary:")
    logger.info(f"  Status: {result.get('status')}")
    if result.get('status') == 'failed':
        logger.error(f"  Error: {result.get('error')}")
    logger.info("="*50)


if __name__ == "__main__":
    main()
