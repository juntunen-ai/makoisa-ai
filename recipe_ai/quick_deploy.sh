#!/bin/bash

# Quick AI Recipe Generator Cloud Run Deployment
# This script builds and deploys using existing project setup

set -e

PROJECT_ID="ruokahinta-scraper-1748695687"
REGION="us-central1"
SERVICE_NAME="ai-recipe-generator"

echo "🚀 Deploying AI Recipe Generator to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if we're in the right directory
if [ ! -d "recipe_ai" ]; then
    echo "❌ Please run this script from the s-kaupat-scraper directory"
    exit 1
fi

echo "🔧 Step 1: Enabling required APIs"
gcloud services enable aiplatform.googleapis.com

echo "🐳 Step 2: Building and deploying with Cloud Run"
gcloud run deploy $SERVICE_NAME \
    --source recipe_ai \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 5 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1,VERTEX_AI_MODEL=gemini-2.0-flash-001,STREAMLIT_SERVER_PORT=8080,STREAMLIT_SERVER_ADDRESS=0.0.0.0,STREAMLIT_BROWSER_GATHER_USAGE_STATS=false,STREAMLIT_SERVER_HEADLESS=true"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "🔗 Your AI Recipe Generator URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
echo ""
echo "📊 Check status: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "📝 View logs: gcloud logs tail --service=$SERVICE_NAME"
