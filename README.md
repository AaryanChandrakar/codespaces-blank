# Plastic Waste Detection for Recycling Automation

A professional, production-grade machine learning project for detecting plastic bottles, bags, and wrappers using YOLOv8. This project is designed to enable automated recycling processes through real-time computer vision inference.

## 🎯 Project Overview

**Objective:** Detect three classes of plastic waste:
- `plastic_bottle` - PET/HDPE bottles
- `plastic_bag` - Single-use plastic bags
- `plastic_wrapper` - Flexible packaging materials

**Tech Stack:**
- **Model:** YOLOv8 (Ultralytics)
- **Data Processing:** Albumentations, OpenCV, Pillow
- **Web Scraping:** icrawler
- **API:** FastAPI + Uvicorn
- **Containerization:** Docker
- **Deployment:** Cloud-ready (supports AWS, GCP, Azure, Render, Fly.io)

## 📁 Project Structure

```
plastic-waste-detection/
├── data/
│   ├── raw/                  # Raw downloaded images
│   │   ├── plastic_bottle/
│   │   ├── plastic_bag/
│   │   └── plastic_wrapper/
│   └── processed/            # YOLO-format dataset
│       ├── images/
│       │   ├── train/
│       │   ├── val/
│       │   └── test/
│       └── labels/
│           ├── train/
│           ├── val/
│           └── test/
├── models/
│   ├── best.pt              # Best trained model
│   └── last.pt              # Last checkpoint
├── src/                      # Source code (modular)
│   ├── __init__.py
│   ├── config_loader.py     # Configuration management
│   ├── scraper.py           # Image web scraping
│   ├── preprocess.py        # Data augmentation & splitting
│   ├── auto_label.py        # Auto-labeling with YOLOv8n
│   ├── train.py             # Model training
│   └── evaluate.py          # Model evaluation & metrics
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── config/
│   └── config.yaml          # Central configuration
├── outputs/
│   └── metrics/             # Evaluation reports & plots
├── main.py                  # CLI orchestrator
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image
├── .gitignore
└── README.md

```

## 🚀 Quick Start

### 1. Installation

**Prerequisites:**
- Python 3.10+
- pip or conda
- (Optional) NVIDIA GPU with CUDA 12.1

**Setup:**

```bash
# Clone repository
git clone https://github.com/your-org/plastic-waste-detection.git
cd plastic-waste-detection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Project

Edit `config/config.yaml` to customize:

```yaml
# Classes to detect
classes:
  - plastic_bottle
  - plastic_bag
  - plastic_wrapper

# Scraping parameters
scraper:
  max_images_per_class: 500

# Training parameters
training:
  epochs: 50
  batch_size: 16
  model_name: "yolov8m"
```

### 3. Run Complete Pipeline

#### Option A: Run Full Pipeline

```bash
python main.py --step all
```

#### Option B: Run Individual Stages

```bash
# Stage 1: Download images from web
python main.py --step scrape

# Stage 2: Preprocess and augment data
python main.py --step preprocess

# Stage 3: Auto-label images (optional, review manually after)
python main.py --step auto_label

# Stage 4: Train the model
python main.py --step train

# Stage 5: Evaluate on test set
python main.py --step evaluate

# Stage 6: Start API server
python main.py --step serve
```

#### Option C: Run Individual Scripts

```bash
# Image scraping
python -m src.scraper

# Preprocessing
python -m src.preprocess

# Auto-labeling
python -m src.auto_label

# Training
python -m src.train

# Evaluation
python -m src.evaluate

# API serving
python -m app.main
```

## 🔍 API Documentation

Once the server is running, visit **http://localhost:8000/docs** for interactive API documentation.

### Endpoints

#### 1. Health Check
```bash
GET /health/

Response:
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": 1699564234.567
}
```

#### 2. Predict (Inference)
```bash
POST /predict/

# Upload image file
curl -X POST "http://localhost:8000/predict/" \
  -F "file=@test_image.jpg"

Response:
{
  "detections": [
    {
      "class_name": "plastic_bottle",
      "confidence": 0.92,
      "bbox": {
        "x1": 100.5,
        "y1": 200.3,
        "x2": 350.8,
        "y2": 500.2,
        "confidence": 0.92
      }
    }
  ],
  "processing_time_ms": 45.3,
  "image_size": [640, 480]
}
```

#### 3. Model Info
```bash
GET /info/

Response:
{
  "classes": ["plastic_bottle", "plastic_bag", "plastic_wrapper"],
  "model_name": "yolov8m",
  "confidence_threshold": 0.5
}
```

## 📊 Training & Evaluation

### Training Output
- **Best model:** `models/best.pt`
- **Training plots:** `runs/detect/plastic_detection/results.png`
- **Logs:** Console output with real-time metrics

### Evaluation Metrics
After training, evaluation generates:
- **Precision, Recall, mAP50, mAP50-95**
- **Confusion matrix** (if using evaluate script)
- **Class-wise performance plots**
- **Report:** `outputs/metrics/evaluation_report.txt`

```bash
# View evaluation report
cat outputs/metrics/evaluation_report.txt
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t plastic-waste-detection:latest .
```

### Run Locally
```bash
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/outputs:/app/outputs \
  plastic-waste-detection:latest
```

### Push to Registry
```bash
# Docker Hub
docker tag plastic-waste-detection:latest username/plastic-waste-detection:latest
docker push username/plastic-waste-detection:latest

# Google Container Registry (GCR)
docker tag plastic-waste-detection:latest gcr.io/project-id/plastic-waste-detection:latest
docker push gcr.io/project-id/plastic-waste-detection:latest

# AWS ECR
docker tag plastic-waste-detection:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/plastic-waste-detection:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/plastic-waste-detection:latest
```

## ☁️ Cloud Deployment

### Option 1: Google Cloud Run (Recommended)
```bash
# Deploy to Cloud Run
gcloud run deploy plastic-waste-detection \
  --image gcr.io/project-id/plastic-waste-detection:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated

# Map custom domain
gcloud run services update-traffic plastic-waste-detection \
  --update-custom-domains plastic-waste.yourdomain.com
```

### Option 2: AWS ECS Fargate
```bash
# Create task definition, service, and load balancer
# See AWS documentation for detailed steps
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Option 3: Render (Simplest)
1. Push image to Docker Hub
2. Create new Web Service on render.com
3. Connect GitHub repo or link Docker image
4. Add custom domain (yourdomain.com → Render)
5. Deploy!

### Option 4: Fly.io
```bash
# Install Fly CLI
brew install flyctl  # or download from fly.io

# Initialize and deploy
fly auth login
fly launch
fly deploy
```

## 🔐 Domain Setup

### 1. Register Domain
- Buy domain from Namecheap, GoDaddy, or similar

### 2. Configure DNS
- Point domain nameservers to your cloud provider
- Or add CNAME record:
  ```
  api.yourdomain.com  CNAME  your-cloud-service.example.com
  ```

### 3. Enable HTTPS
- Cloud providers (GCP, AWS, Render) auto-provision SSL certificates
- Or use Certbot for manual setup

### 4. Test Deployment
```bash
curl https://api.yourdomain.com/health/
curl -X POST https://api.yourdomain.com/predict/ -F "file=@image.jpg"
```

## 📈 Monitoring & Logging

### Local Logging
```bash
# View logs with verbose output
python main.py --step serve --verbose

# Logs are saved to console and optionally to files
```

### Cloud Monitoring (Production)

**Google Cloud Run:**
```bash
gcloud run services describe plastic-waste-detection --format=value(status.url)
gcloud logging read --filter 'resource.service.name="plastic-waste-detection"'
```

**AWS CloudWatch:**
- View logs in CloudWatch dashboard
- Set up alarms for high error rates

**Render/Fly Monitoring:**
- Built-in dashboard with metrics
- Email notifications for failures

## 🧪 Testing

```bash
# Run unit tests
pytest tests/ -v

# Test API locally
python -m pytest tests/test_api.py

# Example inference test
curl -X POST "http://localhost:8000/predict/" \
  -F "file=@tests/sample_images/bottle.jpg" \
  --output response.json
```

## 📝 Data Workflow

1. **Scraping:** `icrawler` downloads images from Bing/Google
2. **Validation:** Corrupt/invalid images removed automatically
3. **Auto-Labeling:** YOLOv8n generates initial YOLO-format labels
4. **Manual Review:** Use LabelImg to correct auto-generated labels
5. **Augmentation:** Albumentations applies transforms during training
6. **Splitting:** 80% train / 10% val / 10% test
7. **Training:** YOLOv8 trained with early stopping
8. **Evaluation:** Metrics computed on held-out test set

## 🎓 Key Features

✅ **Fully Modular:** Each component (scrape, preprocess, train, evaluate, serve) is independent  
✅ **Type Hints:** Full type annotations for IDE support  
✅ **Logging:** Structured logging with levels (INFO, DEBUG, ERROR)  
✅ **Config-Driven:** All hyperparameters in `config.yaml`, no hardcoding  
✅ **Error Handling:** Robust error handling with informative messages  
✅ **Production-Ready:** Includes Dockerfile, health checks, metrics  
✅ **Cloud-Agnostic:** Deploy to any cloud provider  
✅ **API Documentation:** Auto-generated Swagger UI at `/docs`  

## 🔧 Advanced Configuration

### GPU Training
Update `config.yaml`:
```yaml
training:
  device: 0  # GPU device ID (0 for first GPU)
```

### Model Size Selection
```yaml
training:
  model_name: "yolov8n"   # Nano (fastest)
  model_name: "yolov8s"   # Small
  model_name: "yolov8m"   # Medium (recommended)
  model_name: "yolov8l"   # Large
  model_name: "yolov8x"   # Extra Large (slowest, most accurate)
```

### Augmentation Tuning
```yaml
preprocessing:
  augmentation:
    transforms:
      - horizontal_flip: 0.7    # Higher = more flips
      - rotation: 45            # Max rotation in degrees
      - brightness: 0.3         # Brightness range
```

## 📚 References

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Albumentations](https://albumentations.ai/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Google Cloud Run](https://cloud.google.com/run/docs)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open Pull Request

## 📞 Support

For issues, questions, or suggestions:
- Open GitHub issue
- Email: support@yourdomain.com
- Documentation: https://plastic-waste-detection.readthedocs.io

## 🎉 Acknowledgments

Built with:
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://github.com/tiangolo/fastapi)
- [PyTorch](https://pytorch.org/)

---

**Last Updated:** December 2024  
**Version:** 1.0.0  
**Maintainer:** Your Team
