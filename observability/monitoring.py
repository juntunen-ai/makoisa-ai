"""
Google Cloud Monitoring integration for S-kaupat scraper
Provides custom metrics and alerting policies
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

from google.cloud import monitoring_v3
from google.api_core.exceptions import GoogleAPIError
import logging

logger = logging.getLogger(__name__)


class CloudMonitoringIntegration:
    """Integration with Google Cloud Monitoring for custom metrics and alerts"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("Google Cloud Project ID not found")
        
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{self.project_id}"
        
        # Custom metric names
        self.metrics = {
            "scraping_duration": "custom.googleapis.com/scraper/duration_seconds",
            "scraping_success": "custom.googleapis.com/scraper/success_total",
            "scraping_failures": "custom.googleapis.com/scraper/failures_total",
            "stores_scraped": "custom.googleapis.com/scraper/stores_total",
            "bigquery_operations": "custom.googleapis.com/bigquery/operations_total",
            "bigquery_duration": "custom.googleapis.com/bigquery/duration_seconds",
            "api_requests": "custom.googleapis.com/api/requests_total",
            "api_errors": "custom.googleapis.com/api/errors_total"
        }
    
    def create_custom_metrics(self):
        """Create custom metric descriptors"""
        try:
            # Scraping duration metric
            self._create_metric_descriptor(
                self.metrics["scraping_duration"],
                "Scraping operation duration",
                monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                monitoring_v3.MetricDescriptor.ValueType.DOUBLE,
                "s",
                [
                    monitoring_v3.LabelDescriptor(
                        key="store_type",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                        description="Type of store being scraped"
                    ),
                    monitoring_v3.LabelDescriptor(
                        key="success",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.BOOL,
                        description="Whether the operation was successful"
                    )
                ]
            )
            
            # Scraping success counter
            self._create_metric_descriptor(
                self.metrics["scraping_success"],
                "Number of successful scraping operations",
                monitoring_v3.MetricDescriptor.MetricKind.CUMULATIVE,
                monitoring_v3.MetricDescriptor.ValueType.INT64,
                "1",
                [
                    monitoring_v3.LabelDescriptor(
                        key="store_type",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                        description="Type of store being scraped"
                    )
                ]
            )
            
            # Stores scraped gauge
            self._create_metric_descriptor(
                self.metrics["stores_scraped"],
                "Number of stores scraped",
                monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                monitoring_v3.MetricDescriptor.ValueType.INT64,
                "1",
                [
                    monitoring_v3.LabelDescriptor(
                        key="store_type",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                        description="Type of store"
                    )
                ]
            )
            
            # BigQuery operations
            self._create_metric_descriptor(
                self.metrics["bigquery_operations"],
                "BigQuery operations performed",
                monitoring_v3.MetricDescriptor.MetricKind.CUMULATIVE,
                monitoring_v3.MetricDescriptor.ValueType.INT64,
                "1",
                [
                    monitoring_v3.LabelDescriptor(
                        key="operation",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                        description="Type of BigQuery operation"
                    ),
                    monitoring_v3.LabelDescriptor(
                        key="success",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.BOOL,
                        description="Whether the operation was successful"
                    )
                ]
            )
            
            # API requests
            self._create_metric_descriptor(
                self.metrics["api_requests"],
                "HTTP API requests received",
                monitoring_v3.MetricDescriptor.MetricKind.CUMULATIVE,
                monitoring_v3.MetricDescriptor.ValueType.INT64,
                "1",
                [
                    monitoring_v3.LabelDescriptor(
                        key="endpoint",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                        description="API endpoint"
                    ),
                    monitoring_v3.LabelDescriptor(
                        key="status_code",
                        value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                        description="HTTP status code"
                    )
                ]
            )
            
            logger.info("Custom metrics created successfully")
            
        except GoogleAPIError as e:
            logger.error(f"Failed to create custom metrics: {e}")
            raise
    
    def _create_metric_descriptor(self, metric_type: str, description: str,
                                 metric_kind, value_type, unit: str,
                                 labels: list = None):
        """Create a custom metric descriptor"""
        descriptor = monitoring_v3.MetricDescriptor(
            type=metric_type,
            metric_kind=metric_kind,
            value_type=value_type,
            unit=unit,
            description=description,
            labels=labels or []
        )
        
        try:
            self.client.create_metric_descriptor(
                name=self.project_name,
                metric_descriptor=descriptor
            )
            logger.debug(f"Created metric descriptor: {metric_type}")
        except GoogleAPIError as e:
            if "already exists" in str(e).lower():
                logger.debug(f"Metric descriptor already exists: {metric_type}")
            else:
                raise
    
    def write_scraping_metrics(self, duration_seconds: float, store_count: int,
                              store_type: str = None, success: bool = True):
        """Write scraping metrics to Cloud Monitoring"""
        try:
            now = time.time()
            
            # Duration metric
            self._write_time_series(
                self.metrics["scraping_duration"],
                duration_seconds,
                now,
                {"store_type": store_type or "all", "success": str(success).lower()}
            )
            
            # Success counter
            if success:
                self._write_time_series(
                    self.metrics["scraping_success"],
                    1,
                    now,
                    {"store_type": store_type or "all"}
                )
            
            # Store count
            self._write_time_series(
                self.metrics["stores_scraped"],
                store_count,
                now,
                {"store_type": store_type or "all"}
            )
            
        except GoogleAPIError as e:
            logger.error(f"Failed to write scraping metrics: {e}")
    
    def write_bigquery_metrics(self, operation: str, duration_seconds: float,
                              record_count: int = None, success: bool = True):
        """Write BigQuery operation metrics"""
        try:
            now = time.time()
            
            # Operation counter
            self._write_time_series(
                self.metrics["bigquery_operations"],
                1,
                now,
                {"operation": operation, "success": str(success).lower()}
            )
            
            # Duration
            self._write_time_series(
                self.metrics["bigquery_duration"],
                duration_seconds,
                now,
                {"operation": operation, "success": str(success).lower()}
            )
            
        except GoogleAPIError as e:
            logger.error(f"Failed to write BigQuery metrics: {e}")
    
    def write_api_metrics(self, endpoint: str, status_code: int):
        """Write API request metrics"""
        try:
            now = time.time()
            
            self._write_time_series(
                self.metrics["api_requests"],
                1,
                now,
                {"endpoint": endpoint, "status_code": str(status_code)}
            )
            
        except GoogleAPIError as e:
            logger.error(f"Failed to write API metrics: {e}")
    
    def _write_time_series(self, metric_type: str, value: float, timestamp: float,
                          labels: Dict[str, str] = None):
        """Write a time series data point"""
        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type
        series.resource.type = "cloud_run_revision"
        series.resource.labels["project_id"] = self.project_id
        series.resource.labels["service_name"] = "ruokahinta"
        series.resource.labels["revision_name"] = os.getenv("K_REVISION", "unknown")
        series.resource.labels["location"] = os.getenv("FUNCTION_REGION", "europe-north1")
        
        # Add metric labels
        if labels:
            for key, value in labels.items():
                series.metric.labels[key] = value
        
        # Create data point
        point = series.points.add()
        point.value.double_value = value
        point.interval.end_time.seconds = int(timestamp)
        
        # Write the time series
        self.client.create_time_series(
            name=self.project_name,
            time_series=[series]
        )


def create_alerting_policies(project_id: str):
    """Create alerting policies for the scraper service"""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"
    
    policies = []
    
    # High error rate alert
    error_rate_policy = monitoring_v3.AlertPolicy(
        display_name="S-kaupat Scraper - High Error Rate",
        documentation=monitoring_v3.AlertPolicy.Documentation(
            content="Alert when scraper error rate exceeds 10% over 5 minutes",
            mime_type="text/markdown"
        ),
        conditions=[
            monitoring_v3.AlertPolicy.Condition(
                display_name="Error rate > 10%",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter='resource.type="cloud_run_revision" AND resource.label.service_name="s-kaupat-scraper"',
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GREATER_THAN,
                    threshold_value=0.1,
                    duration="300s",
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period="60s",
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_RATE
                        )
                    ]
                )
            )
        ],
        combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.AND,
        enabled=True
    )
    
    # Service down alert
    service_down_policy = monitoring_v3.AlertPolicy(
        display_name="S-kaupat Scraper - Service Down",
        documentation=monitoring_v3.AlertPolicy.Documentation(
            content="Alert when scraper service is not responding to health checks",
            mime_type="text/markdown"
        ),
        conditions=[
            monitoring_v3.AlertPolicy.Condition(
                display_name="Health check failures",
                condition_absent=monitoring_v3.AlertPolicy.Condition.MetricAbsence(
                    filter='resource.type="cloud_run_revision" AND resource.label.service_name="s-kaupat-scraper"',
                    duration="300s",
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period="60s",
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_RATE
                        )
                    ]
                )
            )
        ],
        combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.AND,
        enabled=True
    )
    
    try:
        for policy in [error_rate_policy, service_down_policy]:
            created_policy = client.create_alert_policy(
                name=project_name,
                alert_policy=policy
            )
            logger.info(f"Created alert policy: {created_policy.name}")
            policies.append(created_policy)
        
        return policies
        
    except GoogleAPIError as e:
        logger.error(f"Failed to create alerting policies: {e}")
        raise


# Global monitoring instance
cloud_monitoring = None

def get_cloud_monitoring():
    """Get or create Cloud Monitoring instance"""
    global cloud_monitoring
    
    if cloud_monitoring is None:
        try:
            cloud_monitoring = CloudMonitoringIntegration()
        except Exception as e:
            logger.warning(f"Failed to initialize Cloud Monitoring: {e}")
    
    return cloud_monitoring
