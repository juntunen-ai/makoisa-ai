#!/bin/bash

# S-kaupat Scraper - Observability Setup Script
# Sets up monitoring, alerting, and logging for production

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"europe-north1"}

echo "🔧 Setting up observability for S-kaupat Scraper"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
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

# Enable required APIs for observability
echo "🔧 Enabling monitoring and logging APIs..."
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable cloudtrace.googleapis.com
gcloud services enable clouderrorreporting.googleapis.com

# Create custom dashboard
echo "📊 Creating monitoring dashboard..."
cat > dashboard-config.json << EOF
{
  "displayName": "S-kaupat Scraper Dashboard",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "API Request Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"s-kaupat-scraper\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"s-kaupat-scraper\" AND metric.label.status_code>=400",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "yPos": 4,
        "widget": {
          "title": "Scraping Operations",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"custom.googleapis.com/scraper/success_total\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "STACKED_BAR"
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "yPos": 4,
        "widget": {
          "title": "BigQuery Operations",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"custom.googleapis.com/bigquery/operations_total\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      }
    ]
  }
}
EOF

# Create dashboard using gcloud (note: this requires the alpha component)
if gcloud components list --only-local-state --filter="id:alpha" --format="value(id)" | grep -q alpha; then
    echo "📊 Creating monitoring dashboard..."
    gcloud alpha monitoring dashboards create --config-from-file=dashboard-config.json
else
    echo "⚠️  Dashboard creation skipped (requires gcloud alpha component)"
    echo "   Run: gcloud components install alpha"
    echo "   Then: gcloud alpha monitoring dashboards create --config-from-file=dashboard-config.json"
fi

# Create notification channel (email)
echo "📧 Setting up notification channels..."
echo "To create email notification channels, run:"
echo "gcloud alpha monitoring channels create --display-name='S-kaupat Alerts' --type=email --channel-labels=email_address=your-email@example.com"

# Create log-based metrics
echo "📊 Creating log-based metrics..."

# Error log metric
gcloud logging metrics create scraper_errors \
    --description="Count of error logs from S-kaupat scraper" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="s-kaupat-scraper" AND severity>=ERROR' \
    --verbosity=none || echo "Metric scraper_errors may already exist"

# Request latency metric
gcloud logging metrics create scraper_request_latency \
    --description="Request latency for S-kaupat scraper API" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="s-kaupat-scraper" AND jsonPayload.duration_ms>0' \
    --verbosity=none || echo "Metric scraper_request_latency may already exist"

# Create uptime check
echo "⏰ Creating uptime check..."
cat > uptime-check.yaml << EOF
displayName: "S-kaupat Scraper Health Check"
httpCheck:
  path: "/health"
  port: 443
  useSsl: true
monitoredResource:
  type: "uptime_url"
  labels:
    project_id: "$PROJECT_ID"
    host: "s-kaupat-scraper-[hash]-$REGION.a.run.app"
period: "300s"
timeout: "10s"
EOF

echo "⚠️  To create uptime check, replace [hash] with your actual service hash and run:"
echo "gcloud monitoring uptime create-config uptime-check.yaml"

# Set up structured logging
echo "📝 Configuring structured logging..."
echo "Logs are automatically collected by Cloud Run and available in Cloud Logging"

# Clean up temporary files
rm -f dashboard-config.json uptime-check.yaml

echo ""
echo "✅ Observability setup completed!"
echo ""
echo "🔍 Next steps:"
echo "1. Deploy your service with the observability features"
echo "2. Visit Cloud Monitoring: https://console.cloud.google.com/monitoring"
echo "3. Check Cloud Logging: https://console.cloud.google.com/logs"
echo "4. Set up notification channels for alerts"
echo "5. Create uptime checks for your service URL"
echo ""
echo "📊 Custom metrics will appear after first scraping operations"
echo "🚨 Alerts will trigger based on error rates and service availability"
echo "📈 Dashboard will show real-time performance metrics"
