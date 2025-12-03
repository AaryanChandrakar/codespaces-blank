# GETTING STARTED GUIDE

## 🎯 What You Have

A **production-grade, fully modular ML project** for detecting plastic waste using YOLOv8. This is a complete, professional codebase ready for:
- Local development and testing
- Training on your own data
- Deployment to any cloud provider
- Public API access via a custom domain

---

## 📦 What's Included

### Core Source Code
- **`src/config_loader.py`** - Configuration management
- **`src/scraper.py`** - Download images from web (Bing/Google)
- **`src/preprocess.py`** - Image augmentation & train/val/test splitting
- **`src/auto_label.py`** - Auto-generate YOLO labels with YOLOv8n
- **`src/train.py`** - Train YOLOv8 model
- **`src/evaluate.py`** - Generate metrics & evaluation plots

### API & Deployment
- **`app/main.py`** - FastAPI application with `/predict`, `/health`, `/info` endpoints
- **`Dockerfile`** - Multi-stage Docker image for containerization
- **`docker-compose.yml`** - Local dev environment with optional Jupyter notebook

### Configuration & Orchestration
- **`config/config.yaml`** - Central config file (paths, classes, hyperparameters)
- **`main.py`** - CLI orchestrator for running pipeline stages
- **`requirements.txt`** - All Python dependencies

### Documentation
- **`README.md`** - Complete project documentation
- **`DEPLOYMENT.md`** - Step-by-step cloud deployment guide
- **`tests/client_example.py`** - Example API client code

### Directory Structure
```
data/raw/              → Download images here
data/processed/        → YOLO-format dataset
models/                → Trained models go here
outputs/metrics/       → Evaluation reports & plots
```

---

## 🚀 Quick Start (5 Steps)

### Step 1: Install Dependencies

```bash
cd /workspaces/codespaces-blank
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Download Data

```bash
# Download ~150 images per class from web
python main.py --step scrape
```

**What happens:**
- Images saved to `data/raw/{plastic_bottle, plastic_bag, plastic_wrapper}`
- Corrupt images automatically removed
- Progress logged to console

### Step 3: Prepare Dataset

```bash
# Preprocess & split into train/val/test
python main.py --step preprocess
```

**What happens:**
- Images converted to YOLO format
- 80% train, 10% val, 10% test split
- Auto-augmentation applied to training set
- `data.yaml` created for training

### Step 4: Train Model

```bash
# Train YOLOv8 model (~30-60 min on GPU)
python main.py --step train
```

**What happens:**
- Model training starts with real-time metrics
- Best model saved to `models/best.pt`
- Training plots saved to `runs/detect/plastic_detection/`
- Early stopping after 10 epochs of no improvement

### Step 5: Start API Server

```bash
# Start FastAPI server
python main.py --step serve
```

**What happens:**
- API starts on http://localhost:8000
- Auto-generated docs at http://localhost:8000/docs
- Ready for inference requests!

---

## 🔍 Test the API

### Option A: Interactive Documentation
Open http://localhost:8000/docs and use the "Try it out" button in the UI

### Option B: Command Line
```bash
# Health check
curl http://localhost:8000/health/

# Get API info
curl http://localhost:8000/info/

# Run inference (from another terminal)
curl -X POST http://localhost:8000/predict/ \
  -F "file=@test_image.jpg"
```

### Option C: Python Client
```bash
python tests/client_example.py
```

---

## 📋 Pipeline Stages Explained

| Stage | Command | Duration | Output |
|-------|---------|----------|--------|
| **Scrape** | `python main.py --step scrape` | 10-30 min | Images in `data/raw/` |
| **Preprocess** | `python main.py --step preprocess` | 2-5 min | YOLO format in `data/processed/` |
| **Auto-Label** | `python main.py --step auto_label` | 5-15 min | `.txt` label files (review manually!) |
| **Train** | `python main.py --step train` | 30-120 min | Model saved to `models/best.pt` |
| **Evaluate** | `python main.py --step evaluate` | 5-10 min | Metrics & plots in `outputs/metrics/` |
| **Serve** | `python main.py --step serve` | Instant | API running on port 8000 |

**Run all at once:**
```bash
python main.py --step all
```

---

## ⚙️ Customize Configuration

Edit `config/config.yaml` to adjust:

```yaml
# Model size (n=nano, s=small, m=medium, l=large, x=xlarge)
training:
  model_name: "yolov8m"
  epochs: 50              # More epochs = longer training
  batch_size: 16          # Reduce if out of memory
  img_size: 640

# Augmentation strength
preprocessing:
  augmentation:
    augmentation_factor: 2  # Multiply dataset size with augmentation
    transforms:
      horizontal_flip: 0.5
      rotation: 30
      brightness: 0.2

# API settings
api:
  port: 8000
  confidence_threshold: 0.5  # Higher = fewer detections, higher confidence
```

---

## 🐳 Run with Docker

### Build Image
```bash
docker build -t plastic-waste-detection:latest .
```

### Run Container
```bash
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/outputs:/app/outputs \
  plastic-waste-detection:latest
```

### Use Docker Compose
```bash
docker-compose up -d
# API available at http://localhost:8000
# Jupyter available at http://localhost:8888
```

---

## ☁️ Deploy to Cloud

### 1. **Google Cloud Run** (Recommended - Easiest)
```bash
# See DEPLOYMENT.md for full steps
gcloud run deploy plastic-waste-detection \
  --image gcr.io/your-project/plastic-waste-detection:latest \
  --allow-unauthenticated \
  --region us-central1
```
**Cost:** ~$0.30/million requests  
**Setup time:** 5 minutes

### 2. **Render** (Simplest)
1. Push image to Docker Hub
2. Create Web Service on render.com
3. Connect Docker image
4. Add custom domain
5. Deploy!

### 3. **AWS ECS**, **Fly.io**, others
See `DEPLOYMENT.md` for step-by-step guides

---

## 🎓 How It Works (High-Level)

```
[Web Images]
     ↓
[src/scraper.py] → Download & validate images → data/raw/
     ↓
[src/preprocess.py] → Augment & split data → data/processed/
     ↓
[src/auto_label.py] → Auto-generate labels (review manually!)
     ↓
[src/train.py] → Train YOLOv8 model → models/best.pt
     ↓
[src/evaluate.py] → Compute metrics → outputs/metrics/
     ↓
[app/main.py] → FastAPI server → http://localhost:8000
     ↓
[Deploy to Cloud] → https://api.yourdomain.com
```

---

## 💡 Key Features

✅ **Fully Modular** - Each component works independently  
✅ **Type Hints** - IDE autocomplete & type checking  
✅ **Logging** - Structured logging throughout  
✅ **Error Handling** - Robust error messages  
✅ **Config-Driven** - All settings in `config.yaml`  
✅ **Production-Ready** - Includes health checks, metrics, Docker  
✅ **Cloud-Agnostic** - Deploy anywhere  
✅ **API Docs** - Auto-generated Swagger UI  

---

## 🔧 Troubleshooting

### Issue: "Model not found"
```bash
# Check if model exists
ls -la models/best.pt

# If not, train first
python main.py --step train
```

### Issue: Out of Memory
```yaml
# In config.yaml, reduce batch size
training:
  batch_size: 8  # was 16
```

### Issue: API won't start
```bash
# Check if port 8000 is available
lsof -i :8000
# Kill process if needed: kill -9 <PID>
```

### Issue: Low inference accuracy
```bash
# Check dataset quality
# - More training epochs: epochs: 100
# - Better augmentation: augmentation_factor: 3
# - Larger model: model_name: "yolov8l"
```

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point - orchestrates all steps |
| `config/config.yaml` | Central configuration file |
| `src/config_loader.py` | Load & validate configuration |
| `src/scraper.py` | Download images from web |
| `src/preprocess.py` | Augmentation & dataset splitting |
| `src/auto_label.py` | Generate initial labels with YOLOv8n |
| `src/train.py` | Train YOLOv8 model |
| `src/evaluate.py` | Evaluation & metrics |
| `app/main.py` | FastAPI inference server |
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Local dev environment |
| `requirements.txt` | Python dependencies |
| `README.md` | Full documentation |
| `DEPLOYMENT.md` | Cloud deployment guide |

---

## 🚀 Next Steps

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run pipeline**
   ```bash
   python main.py --step all
   ```

3. **Test API**
   ```bash
   curl http://localhost:8000/health/
   ```

4. **Deploy to cloud**
   - Follow `DEPLOYMENT.md`
   - Map custom domain
   - Share API endpoint with users!

---

## 📞 Support

- **Documentation:** See README.md and DEPLOYMENT.md
- **API Docs:** http://localhost:8000/docs
- **Example Client:** `python tests/client_example.py`
- **Config Reference:** See comments in `config/config.yaml`

---

## 🎉 You're All Set!

Your production-grade plastic waste detection project is ready to use. Start with:

```bash
python main.py --step serve
```

Then visit: **http://localhost:8000/docs**

Enjoy! 🚀
