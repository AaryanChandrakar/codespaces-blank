"""
Example client for testing the Plastic Waste Detection API.
"""
import requests
import json
from pathlib import Path


class PlasticWasteDetectionClient:
    """Client for interacting with the Plastic Waste Detection API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API server.
        """
        self.base_url = base_url.rstrip("/")
    
    def health_check(self) -> dict:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health/")
        response.raise_for_status()
        return response.json()
    
    def get_info(self) -> dict:
        """Get API information and available classes."""
        response = requests.get(f"{self.base_url}/info/")
        response.raise_for_status()
        return response.json()
    
    def predict(self, image_path: str) -> dict:
        """
        Run inference on an image.
        
        Args:
            image_path: Path to image file.
        
        Returns:
            Dictionary with detections.
        """
        with open(image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/predict/", files=files)
        response.raise_for_status()
        return response.json()
    
    def predict_batch(self, image_paths: list) -> list:
        """
        Run inference on multiple images.
        
        Args:
            image_paths: List of image file paths.
        
        Returns:
            List of detection dictionaries.
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.predict(image_path)
                results.append({"image": image_path, "detections": result})
            except Exception as e:
                results.append({"image": image_path, "error": str(e)})
        return results


def main():
    """Example usage of the API client."""
    # Create client
    client = PlasticWasteDetectionClient("http://localhost:8000")
    
    try:
        # Check health
        print("Health Check:")
        health = client.health_check()
        print(json.dumps(health, indent=2))
        print()
        
        # Get API info
        print("API Information:")
        info = client.get_info()
        print(json.dumps(info, indent=2))
        print()
        
        # Run inference (example with a test image)
        test_image = "tests/sample_images/test_bottle.jpg"
        if Path(test_image).exists():
            print(f"Running inference on {test_image}:")
            result = client.predict(test_image)
            print(json.dumps(result, indent=2))
        else:
            print(f"Test image not found: {test_image}")
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server at http://localhost:8000")
        print("Make sure the server is running: python main.py --step serve")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
