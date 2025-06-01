#!/bin/bash

# Simple AI Recipe Generator Cloud Run Deployment Script
# Uses Cloud Run source deployment for faster, more reliable deployment

set -e  # Exit on any error

# Configuration
PROJECT_ID="ruokahinta-scraper-1748695687"
REGION="us-central1"
SERVICE_NAME="ai-recipe-generator"
SERVICE_ACCOUNT="recipe-ai-service@$PROJECT_ID.iam.gserviceaccount.com"

echo "🚀 AI Recipe Generator - Simple Cloud Run Deployment"
echo "Project: $PROJECT_ID"
echo "Region: $REGION" 
echo "Service: $SERVICE_NAME"
echo ""

# Step 1: Set project
echo "📋 Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com aiplatform.googleapis.com bigquery.googleapis.com

# Step 3: Create service account if needed
echo "👤 Setting up service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT 2>/dev/null; then
    echo "Creating service account..."
    gcloud iam service-accounts create recipe-ai-service \
        --display-name="AI Recipe Generator Service Account"
    
    # Grant permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/bigquery.dataViewer"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/bigquery.jobUser"
else
    echo "✅ Service account already exists"
fi

# Step 4: Deploy using source
echo "🚢 Deploying from source..."
cd /Users/harrijuntunen/s-kaupat-scraper/recipe_ai

gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1,VERTEX_AI_MODEL=gemini-2.5-flash-preview-05-20" \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 5 \
    --port 8080

echo ""
echo "✅ Deployment completed!"
echo ""
echo "🔗 Your AI Recipe Generator is available at:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
echo ""
echo "🎉 Ready to generate recipes!"
