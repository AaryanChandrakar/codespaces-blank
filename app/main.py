"""
FastAPI application for plastic waste detection inference.
Provides REST API endpoints for model predictions and health checks.
"""
import logging
import io
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

import numpy as np
from PIL import Image
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from ultralytics import YOLO
except ImportError:
    logging.error("ultralytics not installed. Install with: pip install ultralytics")
    raise

from src.config_loader import load_config

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# Pydantic models
class BoundingBox(BaseModel):
    """Bounding box representation."""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float


class Detection(BaseModel):
    """Single detection result."""
    class_name: str
    confidence: float
    bbox: BoundingBox


class PredictionResponse(BaseModel):
    """Prediction response model."""
    detections: List[Detection]
    processing_time_ms: float
    image_size: tuple


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    model_loaded: bool
    timestamp: float


# Global variables
app = FastAPI(
    title="Plastic Waste Detection API",
    description="YOLOv8-based API for detecting plastic bottles, bags, and wrappers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model and configuration
model = None
config = None
classes = []


def load_model(config_path: str = "config/config.yaml") -> YOLO:
    """
    Load YOLOv8 model for inference.
    
    Args:
        config_path: Path to configuration YAML file.
    
    Returns:
        Loaded YOLO model instance.
    
    Raises:
        FileNotFoundError: If model file not found.
    """
    global config
    config = load_config(config_path)
    
    api_config = config.get("api", {})
    model_path = api_config.get("model_path", "./models/best.pt")
    
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    logger.info(f"Loading model from {model_path}...")
    loaded_model = YOLO(model_path)
    logger.info("Model loaded successfully")
    
    return loaded_model


@app.on_event("startup")
async def startup_event():
    """Initialize model on application startup."""
    global model, classes, config
    
    try:
        model = load_model()
        config = load_config()
        classes = config.get("classes", [])
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


@app.get("/health/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with status and model information.
    """
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        timestamp=time.time()
    )


@app.post("/predict/", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)) -> PredictionResponse:
    """
    Run inference on uploaded image.
    
    Args:
        file: Image file upload.
    
    Returns:
        PredictionResponse with detections and metadata.
    
    Raises:
        HTTPException: If model not loaded or image invalid.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be JPEG or PNG image"
        )
    
    # Validate file size
    api_config = config.get("api", {})
    max_size_mb = api_config.get("max_file_size_mb", 10)
    content = await file.read()
    if len(content) > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
            detail=f"File size exceeds {max_size_mb}MB limit"
        )
    
    try:
        # Load image
        image = Image.open(io.BytesIO(content)).convert("RGB")
        image_array = np.array(image)
        img_height, img_width = image_array.shape[:2]
        
        # Run inference
        start_time = time.time()
        api_config = config.get("api", {})
        conf_threshold = api_config.get("confidence_threshold", 0.5)
        
        results = model(image_array, conf=conf_threshold, verbose=False)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Parse detections
        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Map to project classes or use model class name
                if class_id < len(classes):
                    class_name = classes[class_id]
                else:
                    class_name = model.names.get(class_id, f"class_{class_id}")
                
                # Get bounding box coordinates
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                
                detection = Detection(
                    class_name=class_name,
                    confidence=conf,
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2, confidence=conf)
                )
                detections.append(detection)
        
        logger.info(f"Inference completed: {len(detections)} detections in {processing_time:.2f}ms")
        
        return PredictionResponse(
            detections=detections,
            processing_time_ms=processing_time,
            image_size=(img_width, img_height)
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Plastic Waste Detection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health/",
            "predict": "/predict/",
            "docs": "/docs"
        }
    }


@app.get("/info/")
async def info() -> Dict[str, Any]:
    """Get API information and available classes."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    return {
        "classes": classes,
        "model_name": config.get("training", {}).get("model_name", "unknown"),
        "confidence_threshold": config.get("api", {}).get("confidence_threshold", 0.5),
    }


def create_app(config_path: str = "config/config.yaml") -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        config_path: Path to configuration YAML file.
    
    Returns:
        Configured FastAPI application.
    """
    return app


if __name__ == "__main__":
    import uvicorn
    
    api_config = load_config().get("api", {})
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8000)
    workers = api_config.get("workers", 4)
    
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=False
    )
