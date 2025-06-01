"""
Tests for observability features
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from observability.logging import setup_logging, log_request, log_scraping_metrics, JSONFormatter
from observability.health import HealthChecker
from observability.metrics import MetricsCollector


class TestLogging:
    """Test structured logging functionality"""
    
    def test_json_formatter(self):
        """Test JSON log formatting"""
        formatter = JSONFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"
        
        # Format the record
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify required fields
        assert log_data["severity"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test_logger"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
    
    def test_setup_logging(self):
        """Test logging setup"""
        logger = setup_logging("DEBUG")
        
        assert logger.level == logging.DEBUG
        assert logger.name == "s_kaupat_scraper"
    
    def test_log_request(self, caplog):
        """Test request logging"""
        logger = logging.getLogger("test")
        
        with caplog.at_level(logging.INFO):
            log_request(logger, "/test", {"param": "value"})
        
        assert "Request received: /test" in caplog.text
    
    def test_log_scraping_metrics(self, caplog):
        """Test scraping metrics logging"""
        logger = logging.getLogger("test")
        
        with caplog.at_level(logging.INFO):
            log_scraping_metrics(logger, 83, "prisma", 2500.0)
        
        assert "Scraping completed: 83 stores" in caplog.text


class TestHealthChecker:
    """Test health check functionality"""
    
    @pytest.fixture
    def health_checker(self):
        return HealthChecker()
    
    @pytest.mark.asyncio
    async def test_basic_health(self, health_checker):
        """Test basic health check"""
        health = await health_checker.check_basic_health()
        
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "uptime_seconds" in health
        assert health["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_scraper_health_no_instance(self, health_checker):
        """Test scraper health when not initialized"""
        result = await health_checker._check_scraper_health()
        
        assert result["status"] == "unavailable"
        assert "not initialized" in result["message"]
    
    @pytest.mark.asyncio
    async def test_scraper_health_with_instance(self, health_checker):
        """Test scraper health with mock instance"""
        mock_scraper = Mock()
        health_checker.set_instances(scraper=mock_scraper)
        
        with patch('observability.health.STORE_SELECTORS', {"prisma": {}, "alepa": {}}):
            result = await health_checker._check_scraper_health()
        
        assert result["status"] == "healthy"
        assert result["store_types_available"] == 2
    
    @pytest.mark.asyncio
    async def test_bigquery_health_no_instance(self, health_checker):
        """Test BigQuery health when not initialized"""
        result = await health_checker._check_bigquery_health()
        
        assert result["status"] == "unavailable"
        assert "not initialized" in result["message"]
    
    @pytest.mark.asyncio
    async def test_external_dependencies_health(self, health_checker):
        """Test external dependencies health check"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await health_checker._check_external_dependencies()
        
        assert result["status"] == "healthy"
        assert "s_kaupat_response_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, health_checker):
        """Test readiness probe"""
        mock_scraper = Mock()
        health_checker.set_instances(scraper=mock_scraper)
        
        with patch('observability.health.STORE_SELECTORS', {"prisma": {}}):
            result = await health_checker.check_readiness()
        
        assert "ready" in result
        assert "components" in result
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, health_checker):
        """Test liveness probe"""
        result = await health_checker.check_liveness()
        
        assert result["alive"] is True
        assert "uptime_seconds" in result


class TestMetricsCollector:
    """Test metrics collection functionality"""
    
    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector(retention_hours=1)  # Short retention for testing
    
    def test_record_request(self, metrics_collector):
        """Test request metrics recording"""
        metrics_collector.record_request("/test", 100.0, 200)
        
        metrics = metrics_collector.get_request_metrics()
        
        assert "/test" in metrics
        assert metrics["/test"]["total_requests"] == 1
        assert metrics["/test"]["error_count"] == 0
        assert metrics["/test"]["avg_duration_ms"] == 100.0
    
    def test_record_request_with_error(self, metrics_collector):
        """Test request metrics with error status"""
        metrics_collector.record_request("/test", 150.0, 500)
        
        metrics = metrics_collector.get_request_metrics()
        
        assert metrics["/test"]["total_requests"] == 1
        assert metrics["/test"]["error_count"] == 1
        assert metrics["/test"]["error_rate"] == 1.0
    
    def test_record_scraping(self, metrics_collector):
        """Test scraping metrics recording"""
        metrics_collector.record_scraping(83, "prisma", 2500.0, True)
        
        metrics = metrics_collector.get_scraping_metrics()
        
        assert metrics["total_scrapes"] == 1
        assert metrics["successful_scrapes"] == 1
        assert metrics["success_rate"] == 1.0
        assert metrics["store_counts"]["prisma"] == 83
    
    def test_record_scraping_failure(self, metrics_collector):
        """Test failed scraping metrics"""
        metrics_collector.record_scraping(0, "prisma", 1000.0, False)
        
        metrics = metrics_collector.get_scraping_metrics()
        
        assert metrics["total_scrapes"] == 1
        assert metrics["successful_scrapes"] == 0
        assert metrics["success_rate"] == 0.0
    
    def test_record_bigquery_operation(self, metrics_collector):
        """Test BigQuery operation metrics"""
        metrics_collector.record_bigquery_operation("load", 83, 1500.0, True)
        
        metrics = metrics_collector.get_bigquery_metrics()
        
        assert metrics["total_operations"] == 1
        assert metrics["successful_operations"] == 1
        assert metrics["success_rate"] == 1.0
    
    def test_get_all_metrics(self, metrics_collector):
        """Test complete metrics summary"""
        # Record some test data
        metrics_collector.record_request("/test", 100.0, 200)
        metrics_collector.record_scraping(83, "prisma", 2500.0, True)
        metrics_collector.record_bigquery_operation("load", 83, 1500.0, True)
        
        all_metrics = metrics_collector.get_all_metrics()
        
        assert "timestamp" in all_metrics
        assert "requests" in all_metrics
        assert "scraping" in all_metrics
        assert "bigquery" in all_metrics
    
    def test_metrics_cleanup(self, metrics_collector):
        """Test old metrics cleanup"""
        # Set a very short retention
        metrics_collector.retention_hours = 0.001  # ~3.6 seconds
        
        # Record some metrics
        metrics_collector.record_scraping(83, "prisma", 2500.0, True)
        
        # Verify metrics exist
        metrics = metrics_collector.get_scraping_metrics()
        assert metrics["total_scrapes"] == 1
        
        # Wait for cleanup and record new metric to trigger cleanup
        import time
        time.sleep(4)
        metrics_collector.record_scraping(50, "alepa", 1800.0, True)
        
        # Old metrics should be cleaned up
        metrics = metrics_collector.get_scraping_metrics()
        assert metrics["total_scrapes"] == 1  # Only the new one


class TestObservabilityIntegration:
    """Test integration of observability components"""
    
    def test_metrics_middleware_setup(self):
        """Test that middleware can be created"""
        from server import MetricsMiddleware
        
        mock_app = Mock()
        middleware = MetricsMiddleware(mock_app)
        
        assert middleware.app == mock_app
    
    @patch('observability.monitoring.monitoring_v3')
    def test_cloud_monitoring_integration(self, mock_monitoring):
        """Test Cloud Monitoring integration"""
        from observability.monitoring import CloudMonitoringIntegration
        
        # Mock the client
        mock_client = Mock()
        mock_monitoring.MetricServiceClient.return_value = mock_client
        
        integration = CloudMonitoringIntegration("test-project")
        
        assert integration.project_id == "test-project"
        assert integration.client == mock_client


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
