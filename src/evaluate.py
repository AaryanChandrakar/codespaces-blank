"""
Evaluation module for generating metrics and visualizations on test set.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, precision_recall_curve, average_precision_score
import seaborn as sns

try:
    from ultralytics import YOLO
except ImportError:
    logging.error("ultralytics not installed. Install with: pip install ultralytics")
    raise

from src.config_loader import load_config

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate YOLOv8 model and generate metrics."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize evaluator with configuration.
        
        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = load_config(config_path)
        self.metrics_dir = Path(self.config["project"]["metrics_dir"])
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir = Path(self.config["project"]["models_dir"])
        self.classes = self.config.get("classes", [])
        
        self.eval_config = self.config.get("evaluation", {})
        self.conf_threshold = self.eval_config.get("confidence_threshold", 0.5)
        self.iou_threshold = self.eval_config.get("iou_threshold", 0.45)
    
    def evaluate(self, model_path: str = None, data_yaml: str = "data.yaml") -> Dict[str, Any]:
        """
        Evaluate model on test set.
        
        Args:
            model_path: Path to trained model. If None, uses best.pt from models_dir.
            data_yaml: Path to dataset.yaml file.
        
        Returns:
            Dictionary with evaluation results and metrics.
        """
        if model_path is None:
            model_path = str(self.models_dir / "best.pt")
        
        if not Path(model_path).exists():
            logger.error(f"Model not found: {model_path}")
            return {"status": "failed", "error": "Model not found"}
        
        logger.info(f"Evaluating model: {model_path}")
        
        try:
            model = YOLO(model_path)
            
            # Run validation on test set
            logger.info("Running inference on test set...")
            results = model.val(
                data=data_yaml,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                split="test",
                device=0,
            )
            
            logger.info("Evaluation completed!")
            
            # Extract metrics
            metrics = {
                "mAP50": float(results.box.map50) if hasattr(results.box, 'map50') else None,
                "mAP50_95": float(results.box.map) if hasattr(results.box, 'map') else None,
                "precision": float(results.box.p.mean()) if hasattr(results.box, 'p') else None,
                "recall": float(results.box.r.mean()) if hasattr(results.box, 'r') else None,
            }
            
            # Save metrics
            self._save_metrics(metrics, model_path)
            
            return {"status": "success", "metrics": metrics}
        
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _save_metrics(self, metrics: Dict[str, Any], model_path: str) -> None:
        """
        Save evaluation metrics to JSON and create visualizations.
        
        Args:
            metrics: Dictionary of computed metrics.
            model_path: Path to the evaluated model.
        """
        # Save metrics JSON
        metrics_file = self.metrics_dir / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=4)
        logger.info(f"Metrics saved to: {metrics_file}")
        
        # Create metrics visualization
        self._plot_metrics(metrics)
    
    def _plot_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Create visualization of metrics.
        
        Args:
            metrics: Dictionary of computed metrics.
        """
        if not any(metrics.values()):
            logger.warning("No metrics to plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("Model Evaluation Metrics", fontsize=16)
        
        metric_labels = ["mAP50", "mAP50_95", "Precision", "Recall"]
        metric_keys = ["mAP50", "mAP50_95", "precision", "recall"]
        
        for idx, (ax, label, key) in enumerate(zip(axes.flat, metric_labels, metric_keys)):
            value = metrics.get(key)
            if value is not None:
                ax.barh([0], [value], color='steelblue')
                ax.set_xlim([0, 1])
                ax.set_ylabel(label)
                ax.set_title(f"{label}: {value:.4f}")
            else:
                ax.text(0.5, 0.5, f"{label}: N/A", ha='center', va='center', fontsize=12)
            ax.set_xticks([0, 0.5, 1])
        
        plt.tight_layout()
        plot_file = self.metrics_dir / "metrics_plot.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        logger.info(f"Metrics plot saved to: {plot_file}")
        plt.close()
    
    def generate_report(self, model_path: str = None, data_yaml: str = "data.yaml") -> str:
        """
        Generate comprehensive evaluation report.
        
        Args:
            model_path: Path to trained model.
            data_yaml: Path to dataset.yaml file.
        
        Returns:
            Report as string.
        """
        result = self.evaluate(model_path, data_yaml)
        
        report = "="*60 + "\n"
        report += "PLASTIC WASTE DETECTION - MODEL EVALUATION REPORT\n"
        report += "="*60 + "\n\n"
        
        if result.get("status") == "success":
            metrics = result.get("metrics", {})
            report += "METRICS:\n"
            report += "-"*60 + "\n"
            for key, value in metrics.items():
                if value is not None:
                    report += f"  {key.upper():<20}: {value:.4f}\n"
                else:
                    report += f"  {key.upper():<20}: N/A\n"
        else:
            report += f"ERROR: {result.get('error')}\n"
        
        report += "\n" + "="*60 + "\n"
        
        # Save report
        report_file = self.metrics_dir / "evaluation_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        logger.info(f"Report saved to: {report_file}")
        
        return report


def main(config_path: str = "config/config.yaml", data_yaml: str = "data.yaml"):
    """
    Main entry point for evaluation.
    
    Args:
        config_path: Path to configuration YAML file.
        data_yaml: Path to dataset.yaml file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    evaluator = ModelEvaluator(config_path)
    report = evaluator.generate_report(data_yaml=data_yaml)
    print(report)


if __name__ == "__main__":
    main()
