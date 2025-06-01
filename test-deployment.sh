#!/bin/bash

# Test script for Cloud Run deployment
# Tests all API endpoints after deployment

set -e

SERVICE_URL=${1:-""}

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Please provide the Cloud Run service URL as the first argument"
    echo "Usage: $0 <service-url>"
    echo "Example: $0 https://s-kaupat-scraper-xxx-uc.a.run.app"
    exit 1
fi

echo "🧪 Testing S-kaupat Scraper Cloud Run Deployment"
echo "Service URL: $SERVICE_URL"
echo ""

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -s -f "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Health check passed"
    curl -s "$SERVICE_URL/health" | jq .
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Test root endpoint
echo "🔍 Testing root endpoint..."
if curl -s -f "$SERVICE_URL/" > /dev/null; then
    echo "✅ Root endpoint working"
    curl -s "$SERVICE_URL/" | jq .
else
    echo "❌ Root endpoint failed"
fi
echo ""

# Test store types endpoint
echo "🔍 Testing store types endpoint..."
if curl -s -f "$SERVICE_URL/store-types" > /dev/null; then
    echo "✅ Store types endpoint working"
    curl -s "$SERVICE_URL/store-types" | jq .
else
    echo "❌ Store types endpoint failed"
fi
echo ""

# Test scraping with limit (quick test)
echo "🔍 Testing scraping endpoint (limited)..."
echo "This may take a minute..."
if curl -s -f "$SERVICE_URL/stores?limit=2" > /dev/null; then
    echo "✅ Scraping endpoint working"
    RESULT=$(curl -s "$SERVICE_URL/stores?limit=2")
    echo "Found $(echo "$RESULT" | jq 'length') stores"
    echo "$RESULT" | jq '.[0] // "No stores found"'
else
    echo "❌ Scraping endpoint failed"
fi
echo ""

# Test BigQuery info (if available)
echo "🔍 Testing BigQuery info endpoint..."
if curl -s -f "$SERVICE_URL/bigquery/info" > /dev/null; then
    echo "✅ BigQuery info endpoint working"
    curl -s "$SERVICE_URL/bigquery/info" | jq .
else
    echo "⚠️ BigQuery info endpoint not available (may need setup)"
fi
echo ""

echo "🎉 Testing completed!"
echo ""
echo "📚 Full API documentation: $SERVICE_URL/docs"
echo "📊 Interactive API explorer: $SERVICE_URL/redoc"
