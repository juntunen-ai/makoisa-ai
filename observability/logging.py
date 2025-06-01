"""
Limport json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any configuration for S-kaupat scraper
Provides structured logging with JSON format for Cloud Run
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in Cloud Run"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging(level: str = None) -> logging.Logger:
    """
    Set up structured logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter for Cloud Run, simple formatter for local development
    if os.getenv("ENVIRONMENT") == "production" or os.getenv("K_SERVICE"):
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level))
    
    # Create application logger with explicit level
    logger = logging.getLogger("s_kaupat_scraper")
    logger.setLevel(getattr(logging, level))
    
    return logger


def log_request(logger: logging.Logger, endpoint: str, params: Dict[str, Any] = None):
    """Log incoming request with structured data"""
    logger.info(
        f"Request received: {endpoint}",
        extra={
            "event_type": "request",
            "endpoint": endpoint,
            "params": params or {}
        }
    )


def log_scraping_metrics(logger: logging.Logger, store_count: int, store_type: str = None, 
                        duration_ms: float = None):
    """Log scraping metrics"""
    logger.info(
        f"Scraping completed: {store_count} stores",
        extra={
            "event_type": "scraping_completed",
            "store_count": store_count,
            "store_type": store_type,
            "duration_ms": duration_ms
        }
    )


def log_bigquery_operation(logger: logging.Logger, operation: str, record_count: int = None,
                          duration_ms: float = None, success: bool = True):
    """Log BigQuery operation metrics"""
    logger.info(
        f"BigQuery {operation}: {'success' if success else 'failed'}",
        extra={
            "event_type": "bigquery_operation",
            "operation": operation,
            "record_count": record_count,
            "duration_ms": duration_ms,
            "success": success
        }
    )


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log error with structured context"""
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        },
        exc_info=True
    )
