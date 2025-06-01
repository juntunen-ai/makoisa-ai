#!/bin/bash

# Local development script for Ruokahinta
# Runs the FastAPI server locally for development and testing

set -e

echo "🚀 Starting Ruokahinta Local Development Server"
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Set up environment variables for local development
echo "🔧 Setting up environment..."
export PORT=8080
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-"local-dev"}
export BIGQUERY_DATASET_ID=${BIGQUERY_DATASET_ID:-"s_kaupat"}
export BIGQUERY_TABLE_ID=${BIGQUERY_TABLE_ID:-"stores"}
export BIGQUERY_LOCATION=${BIGQUERY_LOCATION:-"europe-north1"}

echo "Environment variables:"
echo "  PORT: $PORT"
echo "  GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
echo "  BIGQUERY_DATASET_ID: $BIGQUERY_DATASET_ID"
echo "  BIGQUERY_TABLE_ID: $BIGQUERY_TABLE_ID"
echo "  BIGQUERY_LOCATION: $BIGQUERY_LOCATION"
echo ""

# Install Playwright browsers if not already installed
echo "🎭 Setting up Playwright browsers..."
poetry run playwright install chromium

echo "🌐 Starting FastAPI server..."
echo "📚 API Documentation will be available at: http://localhost:8080/docs"
echo "💚 Health Check: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
poetry run python server.py
