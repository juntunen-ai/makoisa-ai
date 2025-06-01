#!/bin/bash

# S-kaupat Scraper Cloud Run Deployment Script
# This script builds and deploys the scraper to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"europe-north1"}
SERVICE_NAME="s-kaupat-scraper"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 S-kaupat Scraper Cloud Run Deployment"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if project is set
if [ "$PROJECT_ID" == "your-project-id" ]; then
    echo "❌ Please provide your Google Cloud Project ID as the first argument"
    echo "Usage: $0 <project-id> [region]"
    exit 1
fi

# Set the project
echo "📋 Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create service account if it doesn't exist
SERVICE_ACCOUNT="s-kaupat-scraper@$PROJECT_ID.iam.gserviceaccount.com"
echo "👤 Setting up service account..."

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &> /dev/null; then
    echo "Creating service account: $SERVICE_ACCOUNT"
    gcloud iam service-accounts create s-kaupat-scraper \
        --display-name="S-kaupat Scraper Service Account" \
        --description="Service account for S-kaupat scraper Cloud Run service"
    
    # Grant BigQuery permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/bigquery.dataEditor"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/bigquery.jobUser"
else
    echo "Service account already exists: $SERVICE_ACCOUNT"
fi

# Create BigQuery dataset if it doesn't exist
echo "📊 Setting up BigQuery dataset..."
if ! bq show --dataset $PROJECT_ID:s_kaupat &> /dev/null; then
    echo "Creating BigQuery dataset: s_kaupat"
    bq mk --dataset --location=$REGION $PROJECT_ID:s_kaupat
else
    echo "BigQuery dataset already exists: s_kaupat"
fi

# Build and push the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."

# Export variables for envsubst
export PROJECT_ID
export REGION

# Replace placeholders in the service YAML
envsubst < cloud-run-service.yaml > cloud-run-service-deployed.yaml

# Deploy the service
gcloud run services replace cloud-run-service-deployed.yaml \
    --region=$REGION

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "📚 API Documentation: $SERVICE_URL/docs"
echo "💚 Health Check: $SERVICE_URL/health"
echo ""
echo "🔧 Example API calls:"
echo "curl $SERVICE_URL/stores?limit=5"
echo "curl $SERVICE_URL/bigquery/info"
echo ""
echo "🧹 To clean up resources later, run:"
echo "gcloud run services delete $SERVICE_NAME --region=$REGION"

# Clean up temporary file
rm -f cloud-run-service-deployed.yaml
