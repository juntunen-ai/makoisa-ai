"""
Metrics collection for S-kaupat scraper
Provides application and business metrics
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import threading
import json


class MetricsCollector:
    """In-memory metrics collector for the S-kaupat scraper"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.lock = threading.Lock()
        
        # Request metrics
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.request_errors = defaultdict(int)
        
        # Scraping metrics
        self.scraping_metrics = deque()
        self.bigquery_metrics = deque()
        
        # Business metrics
        self.store_counts = defaultdict(int)
        self.last_successful_scrape = None
        
    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Record HTTP request metrics"""
        with self.lock:
            self.request_count[endpoint] += 1
            self.request_duration[endpoint].append({
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc),
                "status_code": status_code
            })
            
            if status_code >= 400:
                self.request_errors[endpoint] += 1
            
            # Clean old data
            self._clean_old_request_data(endpoint)
    
    def record_scraping(self, store_count: int, store_type: Optional[str], 
                       duration_ms: float, success: bool = True):
        """Record scraping operation metrics"""
        with self.lock:
            metric = {
                "timestamp": datetime.now(timezone.utc),
                "store_count": store_count,
                "store_type": store_type,
                "duration_ms": duration_ms,
                "success": success
            }
            
            self.scraping_metrics.append(metric)
            
            if success:
                self.last_successful_scrape = datetime.now(timezone.utc)
                if store_type:
                    self.store_counts[store_type] = store_count
                else:
                    self.store_counts["total"] = store_count
            
            self._clean_old_metrics()
    
    def record_bigquery_operation(self, operation: str, record_count: Optional[int],
                                 duration_ms: float, success: bool = True):
        """Record BigQuery operation metrics"""
        with self.lock:
            metric = {
                "timestamp": datetime.now(timezone.utc),
                "operation": operation,
                "record_count": record_count,
                "duration_ms": duration_ms,
                "success": success
            }
            
            self.bigquery_metrics.append(metric)
            self._clean_old_metrics()
    
    def get_request_metrics(self) -> Dict[str, Any]:
        """Get HTTP request metrics summary"""
        with self.lock:
            metrics = {}
            
            for endpoint in self.request_count:
                durations = [
                    d["duration_ms"] for d in self.request_duration[endpoint]
                    if datetime.now(timezone.utc) - d["timestamp"] <= timedelta(hours=self.retention_hours)
                ]
                
                if durations:
                    metrics[endpoint] = {
                        "total_requests": self.request_count[endpoint],
                        "error_count": self.request_errors[endpoint],
                        "error_rate": self.request_errors[endpoint] / self.request_count[endpoint],
                        "avg_duration_ms": sum(durations) / len(durations),
                        "min_duration_ms": min(durations),
                        "max_duration_ms": max(durations),
                        "requests_last_hour": len([
                            d for d in self.request_duration[endpoint]
                            if datetime.now(timezone.utc) - d["timestamp"] <= timedelta(hours=1)
                        ])
                    }
            
            return metrics
    
    def get_scraping_metrics(self) -> Dict[str, Any]:
        """Get scraping metrics summary"""
        with self.lock:
            recent_scrapes = [
                m for m in self.scraping_metrics
                if datetime.now(timezone.utc) - m["timestamp"] <= timedelta(hours=self.retention_hours)
            ]
            
            if not recent_scrapes:
                return {
                    "total_scrapes": 0,
                    "successful_scrapes": 0,
                    "last_successful_scrape": None
                }
            
            successful_scrapes = [m for m in recent_scrapes if m["success"]]
            
            metrics = {
                "total_scrapes": len(recent_scrapes),
                "successful_scrapes": len(successful_scrapes),
                "success_rate": len(successful_scrapes) / len(recent_scrapes),
                "last_successful_scrape": self.last_successful_scrape.isoformat() + "Z" if self.last_successful_scrape else None,
                "store_counts": dict(self.store_counts)
            }
            
            if successful_scrapes:
                durations = [m["duration_ms"] for m in successful_scrapes]
                store_counts = [m["store_count"] for m in successful_scrapes]
                
                metrics.update({
                    "avg_duration_ms": sum(durations) / len(durations),
                    "avg_stores_scraped": sum(store_counts) / len(store_counts),
                    "max_stores_scraped": max(store_counts),
                    "scrapes_last_hour": len([
                        m for m in successful_scrapes
                        if datetime.now(timezone.utc) - m["timestamp"] <= timedelta(hours=1)
                    ])
                })
            
            return metrics
    
    def get_bigquery_metrics(self) -> Dict[str, Any]:
        """Get BigQuery metrics summary"""
        with self.lock:
            recent_operations = [
                m for m in self.bigquery_metrics
                if datetime.now(timezone.utc) - m["timestamp"] <= timedelta(hours=self.retention_hours)
            ]
            
            if not recent_operations:
                return {
                    "total_operations": 0,
                    "successful_operations": 0
                }
            
            successful_operations = [m for m in recent_operations if m["success"]]
            
            metrics = {
                "total_operations": len(recent_operations),
                "successful_operations": len(successful_operations),
                "success_rate": len(successful_operations) / len(recent_operations) if recent_operations else 0
            }
            
            if successful_operations:
                durations = [m["duration_ms"] for m in successful_operations]
                record_counts = [m["record_count"] for m in successful_operations if m["record_count"]]
                
                metrics.update({
                    "avg_duration_ms": sum(durations) / len(durations),
                    "operations_last_hour": len([
                        m for m in successful_operations
                        if datetime.now(timezone.utc) - m["timestamp"] <= timedelta(hours=1)
                    ])
                })
                
                if record_counts:
                    metrics["avg_records_processed"] = sum(record_counts) / len(record_counts)
            
            return metrics
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get complete metrics summary"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "requests": self.get_request_metrics(),
            "scraping": self.get_scraping_metrics(),
            "bigquery": self.get_bigquery_metrics()
        }
    
    def _clean_old_request_data(self, endpoint: str):
        """Clean old request duration data"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        self.request_duration[endpoint] = [
            d for d in self.request_duration[endpoint]
            if d["timestamp"] > cutoff
        ]
    
    def _clean_old_metrics(self):
        """Clean old metrics data"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        
        # Clean scraping metrics
        while self.scraping_metrics and self.scraping_metrics[0]["timestamp"] < cutoff:
            self.scraping_metrics.popleft()
        
        # Clean BigQuery metrics
        while self.bigquery_metrics and self.bigquery_metrics[0]["timestamp"] < cutoff:
            self.bigquery_metrics.popleft()


# Global metrics collector instance
metrics_collector = MetricsCollector()
