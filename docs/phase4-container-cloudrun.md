# Phase 4: Container & Cloud Run Deployment

This phase implements containerization and Cloud Run deployment for the S-kaupat scraper.

## 🎯 Phase 4 Objectives

- ✅ Containerize the application with Docker
- ✅ Create a FastAPI web server for REST API access
- ✅ Deploy to Google Cloud Run
- ✅ Set up service accounts and permissions
- ✅ Create deployment automation scripts
- ✅ Add health checks and monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Run Service                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                FastAPI Server                          ││
│  │  ┌─────────────────────┐  ┌─────────────────────────┐  ││
│  │  │   S-kaupat Scraper  │  │   BigQuery Loader       │  ││
│  │  │   - Web scraping    │  │   - Data loading        │  ││
│  │  │   - Rate limiting   │  │   - Schema validation   │  ││
│  │  │   - Error handling  │  │   - Query operations    │  ││
│  │  └─────────────────────┘  └─────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │    BigQuery         │
                    │    Dataset          │
                    │    s_kaupat.stores  │
                    └─────────────────────┘
```

## 📁 New Files Created

### Core Application
- **`server.py`** - FastAPI web server with REST API endpoints
- **`Dockerfile`** - Multi-stage Docker container definition
- **`docker-compose.yml`** - Local development with Docker Compose

### Cloud Run Deployment
- **`cloud-run-service.yaml`** - Kubernetes service definition for Cloud Run
- **`deploy.sh`** - Automated deployment script
- **`test-deployment.sh`** - Post-deployment testing script

### Development
- **`dev.sh`** - Local development server startup
- **`.dockerignore`** - Docker build optimization
- **`tests/test_server.py`** - FastAPI server tests

## 🚀 API Endpoints

The FastAPI server provides the following REST API endpoints:

### Health & Info
- `GET /` - Service information and health status
- `GET /health` - Detailed health check
- `GET /store-types` - List available store types

### Scraping
- `GET /stores` - Scrape stores from S-kaupat.fi
  - `?store_type=prisma` - Filter by store type
  - `?limit=10` - Limit number of results

### BigQuery Operations
- `POST /bigquery/load` - Scrape and load data to BigQuery
- `GET /bigquery/query` - Query stores from BigQuery
- `GET /bigquery/info` - Get dataset and table information

## 🐳 Docker Container

The Docker container includes:
- **Python 3.12 slim** base image for minimal size
- **Poetry** for dependency management
- **Playwright** with Chromium browser for web scraping
- **Non-root user** for security
- **Health checks** for Cloud Run compatibility

### Build locally:
```bash
docker build -t s-kaupat-scraper .
```

### Run locally:
```bash
docker-compose up
```

## ☁️ Cloud Run Deployment

### Prerequisites
1. Google Cloud Project with billing enabled
2. gcloud CLI installed and configured
3. Docker installed for building images

### Automated Deployment
```bash
./deploy.sh your-project-id europe-north1
```

The deployment script:
1. ✅ Enables required Google Cloud APIs
2. ✅ Creates service account with BigQuery permissions
3. ✅ Sets up BigQuery dataset
4. ✅ Builds and pushes Docker image
5. ✅ Deploys to Cloud Run
6. ✅ Returns service URL for testing

### Manual Deployment
```bash
# Build and push image
docker build -t gcr.io/your-project/s-kaupat-scraper .
docker push gcr.io/your-project/s-kaupat-scraper

# Deploy to Cloud Run
gcloud run services replace cloud-run-service.yaml --region=europe-north1
```

## 🔧 Configuration

### Environment Variables
- `PORT` - Server port (default: 8080)
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `BIGQUERY_DATASET_ID` - BigQuery dataset (default: s_kaupat)
- `BIGQUERY_TABLE_ID` - BigQuery table (default: stores)
- `BIGQUERY_LOCATION` - BigQuery location (default: europe-north1)

### Cloud Run Features
- **Auto-scaling**: 0-10 instances based on traffic
- **Resource limits**: 2 CPU, 2GB memory
- **Timeout**: 5 minutes for long scraping operations
- **Health checks**: Automatic health monitoring
- **Service account**: Dedicated IAM for BigQuery access

## 🧪 Testing

### Local Testing
```bash
# Start development server
./dev.sh

# Run tests
poetry run pytest tests/test_server.py
```

### Cloud Run Testing
```bash
# Test deployed service
./test-deployment.sh https://your-service-url.run.app
```

### API Documentation
Once deployed, visit:
- `https://your-service-url.run.app/docs` - Interactive API documentation
- `https://your-service-url.run.app/redoc` - Alternative API docs

## 💰 Cost Optimization

Cloud Run pricing is based on:
- **CPU allocation**: Only charged during request processing
- **Memory**: Optimized with 1-2GB allocation
- **Requests**: Pay per request, free tier available
- **Auto-scaling**: Scales to zero when not in use

Estimated costs for moderate usage (~100 requests/month):
- **Cloud Run**: $0-5/month
- **Container Registry**: $0-1/month  
- **BigQuery**: $0-10/month (depending on data volume)

## 🔒 Security Features

- **Non-root container user** - Enhanced security
- **Service account isolation** - Minimal required permissions
- **Environment variable secrets** - No hardcoded credentials
- **HTTPS only** - All Cloud Run traffic encrypted
- **VPC connector ready** - Can be configured for private networking

## 📊 Monitoring

Cloud Run provides built-in monitoring:
- **Request metrics** - Latency, error rates, request count
- **Resource usage** - CPU, memory utilization
- **Health checks** - Automatic service health monitoring
- **Logs** - Structured logging with Cloud Logging integration

## 🚀 Example Usage

After deployment, you can use the API:

```bash
# Get service info
curl https://your-service-url.run.app/

# Scrape 5 Prisma stores
curl "https://your-service-url.run.app/stores?store_type=prisma&limit=5"

# Load data to BigQuery
curl -X POST "https://your-service-url.run.app/bigquery/load?store_type=prisma"

# Query BigQuery data
curl "https://your-service-url.run.app/bigquery/query?city=Helsinki&limit=10"
```

## ✅ Phase 4 Complete

Phase 4 successfully implements:
- ✅ **Containerized application** with Docker
- ✅ **FastAPI REST API** with comprehensive endpoints
- ✅ **Cloud Run deployment** with auto-scaling
- ✅ **Automated deployment scripts** for easy setup
- ✅ **Health checks and monitoring** for production readiness
- ✅ **Security best practices** with service accounts
- ✅ **Cost optimization** with efficient resource usage
- ✅ **Testing scripts** for validation

**Next Phase**: Phase 5 - Infrastructure as Code with Terraform
