#!/bin/bash

# AI Recipe Generator Cloud Run Deployment Script
# This script builds and deploys the AI Recipe Generator to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID=${1:-"ruokahinta-scraper-1748695687"}
REGION=${2:-"us-central1"}
SERVICE_NAME="ai-recipe-generator"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
SERVICE_ACCOUNT="recipe-ai-service@$PROJECT_ID.iam.gserviceaccount.com"

echo "🚀 AI Recipe Generator Cloud Run Deployment"
echo "Project: $PROJECT_ID"
echo "Region: $REGION" 
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo "Service Account: $SERVICE_ACCOUNT"
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

echo "📋 Step 1: Setting up Google Cloud project"
gcloud config set project $PROJECT_ID

echo "🔧 Step 2: Enabling required APIs"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    containerregistry.googleapis.com

echo "👤 Step 3: Creating service account (if it doesn't exist)"
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT 2>/dev/null; then
    echo "Creating service account: $SERVICE_ACCOUNT"
    gcloud iam service-accounts create recipe-ai-service \
        --display-name="AI Recipe Generator Service Account" \
        --description="Service account for AI Recipe Generator with Vertex AI and BigQuery access"
else
    echo "✅ Service account already exists: $SERVICE_ACCOUNT"
fi

echo "🔑 Step 4: Granting necessary permissions"
# Vertex AI permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"

# BigQuery permissions  
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.jobUser"

echo "🐳 Step 5: Building Docker image"
cd /Users/harrijuntunen/s-kaupat-scraper

# Build the image using Cloud Build for better performance
gcloud builds submit \
    --config recipe_ai/cloudbuild.yaml \
    --substitutions _SERVICE_NAME=$SERVICE_NAME,_PROJECT_ID=$PROJECT_ID \
    .

echo "🚢 Step 6: Deploying to Cloud Run"
# Replace variables in the service configuration
envsubst < recipe_ai/cloud-run-service.yaml > recipe_ai/cloud-run-service-deployed.yaml

# Deploy the service
gcloud run services replace recipe_ai/cloud-run-service-deployed.yaml \
    --region=$REGION

echo "🌐 Step 7: Making the service publicly accessible"
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="allUsers" \
    --role="roles/run.invoker"

echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Your AI Recipe Generator is now available at:"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "$SERVICE_URL"
echo ""
echo "📊 To check the status:"
echo "gcloud run services describe $SERVICE_NAME --region=$REGION"
echo ""
echo "📝 To view logs:"
echo "gcloud logs tail --service=$SERVICE_NAME"
echo ""
echo "🎉 Happy recipe generating!"
