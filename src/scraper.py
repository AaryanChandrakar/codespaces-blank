"""
Web scraper module for acquiring plastic waste images using icrawler.
Supports Bing and Google image search backends with error handling for corrupt images.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List
from PIL import Image
import io

try:
    from icrawler.builtin import BingImageCrawler, GoogleImageCrawler
except ImportError:
    logging.error("icrawler not installed. Install with: pip install icrawler")
    raise

from src.config_loader import load_config

logger = logging.getLogger(__name__)


class ImageScraper:
    """Scrape images from web for each plastic waste class."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the scraper with configuration.
        
        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = load_config(config_path)
        self.raw_dir = Path(self.config["project"]["raw_dir"])
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        self.scraper_config = self.config.get("scraper", {})
        self.max_images = self.scraper_config.get("max_images_per_class", 500)
        self.timeout = self.scraper_config.get("timeout", 10)
        self.extensions = self.scraper_config.get("image_extensions", [".jpg", ".jpeg", ".png"])
        self.min_size = self.scraper_config.get("min_image_size", 50)
    
    def _validate_image(self, image_path: str) -> bool:
        """
        Validate that downloaded image is not corrupt and meets size requirements.
        
        Args:
            image_path: Path to image file.
        
        Returns:
            True if image is valid, False otherwise.
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
                # Reopen to check dimensions
                img = Image.open(image_path)
                if img.size[0] < self.min_size or img.size[1] < self.min_size:
                    logger.warning(f"Image too small ({img.size}): {image_path}")
                    return False
                logger.debug(f"Image validated: {image_path} ({img.size})")
                return True
        except Exception as e:
            logger.warning(f"Invalid image file {image_path}: {e}")
            return False
    
    def _clean_corrupt_images(self, class_dir: Path) -> None:
        """
        Remove corrupt images from a class directory.
        
        Args:
            class_dir: Directory containing downloaded images.
        """
        for img_file in class_dir.glob("*"):
            if img_file.suffix.lower() in self.extensions:
                if not self._validate_image(str(img_file)):
                    try:
                        img_file.unlink()
                        logger.info(f"Removed corrupt image: {img_file}")
                    except Exception as e:
                        logger.error(f"Failed to delete {img_file}: {e}")
    
    def scrape_images(self) -> Dict[str, int]:
        """
        Scrape images for each class using Bing Image Search.
        Falls back to GoogleImageCrawler if Bing fails.
        
        Returns:
            Dictionary with class names and count of downloaded images.
        """
        search_queries = self.scraper_config.get("search_queries", {})
        results = {}
        
        for class_name, keywords in search_queries.items():
            class_dir = self.raw_dir / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Scraping images for class: {class_name}")
            
            for keyword in keywords:
                try:
                    logger.info(f"  Searching for: '{keyword}'")
                    
                    # Try Bing first
                    try:
                        bing_crawler = BingImageCrawler(storage={"root_dir": str(class_dir)})
                        bing_crawler.crawl(
                            keyword=keyword,
                            max_num=self.max_images // len(keywords)
                        )
                        logger.info(f"  Bing search completed for '{keyword}'")
                    except Exception as bing_error:
                        logger.warning(f"Bing crawl failed for '{keyword}': {bing_error}")
                        # Fallback to Google
                        try:
                            google_crawler = GoogleImageCrawler(storage={"root_dir": str(class_dir)})
                            google_crawler.crawl(
                                keyword=keyword,
                                max_num=self.max_images // len(keywords)
                            )
                            logger.info(f"  Google search completed for '{keyword}'")
                        except Exception as google_error:
                            logger.error(f"Both Bing and Google crawls failed for '{keyword}': {google_error}")
                
                except Exception as e:
                    logger.error(f"Error scraping '{keyword}' for {class_name}: {e}")
            
            # Validate and clean corrupt images
            logger.info(f"Validating images for {class_name}...")
            self._clean_corrupt_images(class_dir)
            
            image_count = len(list(class_dir.glob("*")))
            results[class_name] = image_count
            logger.info(f"Completed {class_name}: {image_count} images")
        
        return results
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get current statistics of downloaded images per class.
        
        Returns:
            Dictionary with class names and image counts.
        """
        stats = {}
        for class_dir in self.raw_dir.iterdir():
            if class_dir.is_dir():
                image_count = len(list(class_dir.glob("*")))
                stats[class_dir.name] = image_count
        return stats


def main(config_path: str = "config/config.yaml"):
    """
    Main entry point for image scraping.
    
    Args:
        config_path: Path to configuration YAML file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    scraper = ImageScraper(config_path)
    results = scraper.scrape_images()
    
    logger.info("="*50)
    logger.info("Scraping Summary:")
    for class_name, count in results.items():
        logger.info(f"  {class_name}: {count} images")
    logger.info("="*50)


if __name__ == "__main__":
    main()
