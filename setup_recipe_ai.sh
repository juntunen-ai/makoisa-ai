#!/bin/bash

# AI Recipe Generator Setup Script
echo "🍳 Setting up AI Recipe Generator..."

# Check if Google Cloud SDK is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found. Please install it first:"
    echo "   brew install google-cloud-sdk"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "🔐 Please authenticate with Google Cloud:"
    echo "   gcloud auth login"
    echo "   gcloud auth application-default login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No active Google Cloud project found. Set one with:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Using Google Cloud project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com --quiet
gcloud services enable bigquery.googleapis.com --quiet

# Check if BigQuery table exists
TABLE_EXISTS=$(bq ls -d ${PROJECT_ID}:s_kaupat 2>/dev/null | grep -c "s_kaupat" || echo "0")
if [ "$TABLE_EXISTS" = "0" ]; then
    echo "⚠️  Warning: BigQuery dataset 's_kaupat' not found."
    echo "   Make sure your S-kaupat scraper has populated the BigQuery table."
fi

# Create environment file
echo "📝 Creating environment configuration..."
cat > recipe_ai/.env << EOF
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
BIGQUERY_TABLE=${PROJECT_ID}.s_kaupat.products

# Vertex AI Configuration  
VERTEX_AI_LOCATION=europe-west4
VERTEX_AI_MODEL=gemini-1.5-pro

# Recipe AI Settings
MAX_PRICE_RESULTS=10
DEFAULT_SERVINGS=4
EOF

echo "✅ Setup complete!"
echo ""
echo "🚀 To run the AI Recipe Generator:"
echo "   cd /Users/harrijuntunen/s-kaupat-scraper"
echo "   poetry run streamlit run recipe_ai/ui/app.py"
echo ""
echo "📖 Or test the core functionality:"
echo "   poetry run python -c \"from recipe_ai import RecipeGenerator; rg = RecipeGenerator(); print(rg.generate_recipe('I want chicken pasta'))\""
