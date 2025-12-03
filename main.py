"""
Main orchestrator script for Plastic Waste Detection pipeline.
Provides CLI interface to run different stages: scrape, preprocess, train, evaluate, serve.
"""
import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point with CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Plastic Waste Detection - Complete ML Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --step scrape
  python main.py --step preprocess
  python main.py --step train
  python main.py --step evaluate
  python main.py --step serve
  python main.py --step all
        """
    )
    
    parser.add_argument(
        "--step",
        type=str,
        default="all",
        choices=["scrape", "preprocess", "auto_label", "train", "evaluate", "serve", "all"],
        help="Pipeline step to execute"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--data_yaml",
        type=str,
        default="data.yaml",
        help="Path to YOLO dataset.yaml file"
    )
    
    parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to trained model for evaluation/serving"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("="*70)
    logger.info("PLASTIC WASTE DETECTION - ML PIPELINE ORCHESTRATOR")
    logger.info("="*70)
    
    try:
        if args.step in ["scrape", "all"]:
            run_scrape(args.config)
        
        if args.step in ["preprocess", "all"]:
            run_preprocess(args.config)
        
        if args.step in ["auto_label", "all"]:
            run_auto_label(args.config)
        
        if args.step in ["train", "all"]:
            run_train(args.config, args.data_yaml)
        
        if args.step in ["evaluate", "all"]:
            run_evaluate(args.config, args.data_yaml, args.model_path)
        
        if args.step == "serve":
            run_serve(args.config)
        
        logger.info("="*70)
        logger.info("Pipeline execution completed successfully!")
        logger.info("="*70)
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


def run_scrape(config_path: str) -> None:
    """
    Execute image scraping stage.
    
    Args:
        config_path: Path to configuration file.
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 1: DATA SCRAPING")
    logger.info("="*70)
    
    try:
        from src.scraper import ImageScraper
        
        logger.info("Initializing image scraper...")
        scraper = ImageScraper(config_path)
        
        logger.info("Starting image acquisition from web...")
        results = scraper.scrape_images()
        
        logger.info("Scraping Summary:")
        for class_name, count in results.items():
            logger.info(f"  {class_name}: {count} images")
    
    except ImportError as e:
        logger.error(f"Dependency error: {e}")
        logger.error("Ensure icrawler is installed: pip install icrawler")
        raise
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


def run_preprocess(config_path: str) -> None:
    """
    Execute preprocessing stage.
    
    Args:
        config_path: Path to configuration file.
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 2: DATA PREPROCESSING")
    logger.info("="*70)
    
    try:
        from src.preprocess import DataPreprocessor
        
        logger.info("Initializing data preprocessor...")
        preprocessor = DataPreprocessor(config_path)
        
        logger.info("Starting preprocessing and augmentation...")
        stats = preprocessor.preprocess_and_split()
        
        logger.info("Preprocessing Summary:")
        for split, count in stats.items():
            logger.info(f"  {split}: {count} images")
        
        logger.info("Saving dataset.yaml...")
        preprocessor.save_dataset_yaml("data.yaml")
    
    except ImportError as e:
        logger.error(f"Dependency error: {e}")
        logger.error("Ensure albumentations is installed: pip install albumentations")
        raise
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise


def run_auto_label(config_path: str) -> None:
    """
    Execute auto-labeling stage.
    
    Args:
        config_path: Path to configuration file.
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 3: AUTO-LABELING")
    logger.info("="*70)
    
    try:
        from src.auto_label import AutoLabeler
        
        logger.info("Initializing auto-labeler...")
        labeler = AutoLabeler(config_path)
        
        logger.info("Starting auto-labeling with YOLOv8n...")
        results = labeler.auto_label_all()
        
        logger.info("Auto-Labeling Summary:")
        total_images = 0
        total_labeled = 0
        for class_name, (total, labeled) in results.items():
            logger.info(f"  {class_name}: {labeled}/{total} labeled")
            total_images += total
            total_labeled += labeled
        
        logger.info(f"Total: {total_labeled}/{total_images} images labeled")
        logger.info("\nNote: Please review and correct labels manually using LabelImg or similar tool.")
    
    except Exception as e:
        logger.error(f"Auto-labeling failed: {e}")
        raise


def run_train(config_path: str, data_yaml: str) -> None:
    """
    Execute training stage.
    
    Args:
        config_path: Path to configuration file.
        data_yaml: Path to dataset YAML file.
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 4: MODEL TRAINING")
    logger.info("="*70)
    
    try:
        from src.train import ModelTrainer
        
        if not Path(data_yaml).exists():
            raise FileNotFoundError(f"Dataset YAML not found: {data_yaml}")
        
        logger.info("Initializing model trainer...")
        trainer = ModelTrainer(config_path)
        
        logger.info("Starting model training...")
        result = trainer.train(data_yaml)
        
        if result.get("status") == "success":
            logger.info("Training completed successfully!")
        else:
            raise RuntimeError(f"Training failed: {result.get('error')}")
    
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


def run_evaluate(config_path: str, data_yaml: str, model_path: str = None) -> None:
    """
    Execute evaluation stage.
    
    Args:
        config_path: Path to configuration file.
        data_yaml: Path to dataset YAML file.
        model_path: Optional path to specific model.
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 5: MODEL EVALUATION")
    logger.info("="*70)
    
    try:
        from src.evaluate import ModelEvaluator
        
        logger.info("Initializing model evaluator...")
        evaluator = ModelEvaluator(config_path)
        
        logger.info("Generating evaluation report...")
        report = evaluator.generate_report(model_path, data_yaml)
        print(report)
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


def run_serve(config_path: str) -> None:
    """
    Execute API serving stage.
    
    Args:
        config_path: Path to configuration file.
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 6: API SERVING")
    logger.info("="*70)
    
    try:
        import uvicorn
        from src.config_loader import load_config
        
        config = load_config(config_path)
        api_config = config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 8000)
        workers = api_config.get("workers", 4)
        
        logger.info(f"Starting FastAPI server on {host}:{port}...")
        logger.info("API Documentation: http://localhost:8000/docs")
        
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            workers=workers,
            reload=False,
            log_level="info"
        )
    
    except Exception as e:
        logger.error(f"API serving failed: {e}")
        raise


if __name__ == "__main__":
    main()