# Cloud Deployment Guide

## Pre-Deployment Checklist

- [ ] Model trained and saved to `models/best.pt`
- [ ] All tests passing
- [ ] Docker image builds successfully
- [ ] Environment variables configured
- [ ] Domain name registered
- [ ] Cloud provider account created

---

## 1. Google Cloud Run (Recommended for Beginners)

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Docker image pushed to GCR

### Deployment Steps

```bash
# 1. Set project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# 3. Build and push image to GCR
docker build -t gcr.io/$PROJECT_ID/plastic-waste-detection:latest .
docker push gcr.io/$PROJECT_ID/plastic-waste-detection:latest

# 4. Deploy to Cloud Run
gcloud run deploy plastic-waste-detection \
  --image gcr.io/$PROJECT_ID/plastic-waste-detection:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --allow-unauthenticated \
  --set-env-vars "PORT=8000"

# 5. Get service URL
gcloud run services describe plastic-waste-detection --region us-central1 --format 'value(status.url)'
```

### Map Custom Domain

```bash
# 1. Verify domain ownership in Google Cloud Console
# (Add DNS records to your domain registrar)

# 2. Create domain mapping
gcloud run domain-mappings create \
  --service=plastic-waste-detection \
  --domain=api.yourdomain.com \
  --region=us-central1

# 3. Update DNS records (follow gcloud output)
```

---

## 2. AWS ECS Fargate

### Prerequisites
- AWS account
- `aws` CLI configured
- ECR repository created

### Deployment Steps

```bash
# 1. Push image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker build -t plastic-waste-detection:latest .
docker tag plastic-waste-detection:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/plastic-waste-detection:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/plastic-waste-detection:latest

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name plastic-waste-cluster

# 3. Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 4. Create service
aws ecs create-service \
  --cluster plastic-waste-cluster \
  --service-name plastic-waste-service \
  --task-definition plastic-waste-detection:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"

# 5. Update Application Load Balancer (ALB)
# Configure target group and map custom domain via Route53
```

---

## 3. Render (Simplest Deployment)

### Prerequisites
- Render account
- Docker image on Docker Hub

### Deployment Steps

1. **Push to Docker Hub:**
   ```bash
   docker build -t yourusername/plastic-waste-detection:latest .
   docker push yourusername/plastic-waste-detection:latest
   ```

2. **Create Web Service on Render:**
   - Go to render.com
   - Click "New +" → "Web Service"
   - Select "Deploy an existing image"
   - Enter: `yourusername/plastic-waste-detection:latest`
   - Set Plan: "Standard" (recommended)
   - Port: 8000
   - Environment: 
     - `PYTHONUNBUFFERED=1`
   - Create Service

3. **Map Custom Domain:**
   - In Render dashboard → Settings → Custom Domains
   - Add your domain: `api.yourdomain.com`
   - Update DNS with CNAME record pointing to Render URL

---

## 4. Fly.io (Modern Alternative)

### Prerequisites
- Fly account
- flyctl CLI installed

### Deployment Steps

```bash
# 1. Login to Fly
fly auth login

# 2. Create fly.toml configuration
cat > fly.toml << EOF
app = "plastic-waste-detection"
kill_signal = "SIGINT"
kill_timeout = 5
processes = {}

[build]
  image = "plastic-waste-detection:latest"

[build.args]
  buildkit = "true"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []
  
  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"
  
  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80
  
  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

[[statics]]
  guest_path = "/app/models"
  url_prefix = "/models"
EOF

# 3. Deploy
fly launch  # First time only
fly deploy

# 4. Map custom domain
fly certs create api.yourdomain.com
```

---

## 5. CI/CD Pipeline (GitHub Actions)

### Setup GitHub Actions for Auto-Deployment

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        run: |
          docker build -t ${{ secrets.REGISTRY }}/plastic-waste-detection:latest .
          docker push ${{ secrets.REGISTRY }}/plastic-waste-detection:latest
      
      - name: Deploy to Cloud Run
        run: |
          gcloud auth activate-service-account --key-file=${{ secrets.GCP_SA_KEY }}
          gcloud run deploy plastic-waste-detection \
            --image=${{ secrets.REGISTRY }}/plastic-waste-detection:latest \
            --platform=managed \
            --region=us-central1 \
            --allow-unauthenticated
```

### Add GitHub Secrets:
- `REGISTRY`: `gcr.io/your-project-id`
- `GCP_SA_KEY`: Service account JSON key

---

## 6. Environment Variables

Create `.env` file in cloud environment:

```
# Model configuration
MODEL_PATH=/app/models/best.pt
CONFIDENCE_THRESHOLD=0.5

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logging
LOG_LEVEL=INFO

# Optional: Authentication
API_KEY=your-secret-key
```

---

## 7. Monitoring & Observability

### Google Cloud Run
```bash
# View logs
gcloud run services logs read plastic-waste-detection --region us-central1

# Set up alerts
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="API Error Rate" \
  --condition=...
```

### AWS CloudWatch
```bash
# View logs
aws logs tail /ecs/plastic-waste-task --follow
```

### Render/Fly Built-in Dashboards
- Available in web console
- Email notifications for failures

---

## 8. Testing Deployment

```bash
# Health check
curl https://api.yourdomain.com/health/

# API info
curl https://api.yourdomain.com/info/

# Run inference
curl -X POST https://api.yourdomain.com/predict/ \
  -F "file=@test_image.jpg" \
  -H "Authorization: Bearer YOUR_API_KEY"  # if auth enabled
```

---

## 9. Scaling Configuration

### Horizontal Scaling
```yaml
# For Google Cloud Run
gcloud run services update plastic-waste-detection \
  --max-instances=100 \
  --min-instances=1
```

### Auto-scaling
- **Google Cloud Run:** Automatic (based on request volume)
- **AWS ECS:** Configure target tracking scaling
- **Render:** Manual or pay-as-you-go

---

## 10. Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check service logs, restart deployment |
| Timeout errors | Increase timeout in cloud config |
| Out of memory | Increase allocated memory (2Gi → 4Gi) |
| High latency | Enable caching, upgrade model to smaller variant (YOLOv8n) |
| Model not found | Verify `models/best.pt` exists, check volume mounts |

---

## Summary

| Platform | Ease | Cost | Performance | Recommendation |
|----------|------|------|-------------|---|
| Google Cloud Run | ⭐⭐⭐⭐⭐ | $ | ⭐⭐⭐⭐ | Best for beginners |
| AWS ECS | ⭐⭐⭐ | $$ | ⭐⭐⭐⭐⭐ | Enterprise |
| Render | ⭐⭐⭐⭐⭐ | $ | ⭐⭐⭐ | Simplest |
| Fly.io | ⭐⭐⭐⭐ | $ | ⭐⭐⭐⭐ | Modern, fast |

For more help, see README.md or check official cloud provider documentation.
