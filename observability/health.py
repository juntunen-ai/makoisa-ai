"""
Health check module for comprehensive service monitoring
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

import httpx
from google.cloud import bigquery

# Store types configuration for health checks
STORE_SELECTORS = {
    "prisma": {},
    "s-market": {},
    "alepa": {},
    "sale": {}, 
    "food-market-herkku": {},
    "sokos-herkku": {},
    "mestarin-herkku": {}
}


logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health checker for the Ruokahinta service"""
    
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.scraper_instance = None
        self.bq_loader_instance = None
    
    def set_instances(self, scraper=None, bq_loader=None):
        """Set service instances for health checking"""
        self.scraper_instance = scraper
        self.bq_loader_instance = bq_loader
    
    async def check_basic_health(self) -> Dict[str, Any]:
        """Basic health check - service is running"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "version": "1.0.0"
        }
    
    async def check_detailed_health(self) -> Dict[str, Any]:
        """Detailed health check with component status"""
        health_data = await self.check_basic_health()
        
        # Check components
        components = {}
        
        # Scraper health
        components["scraper"] = await self._check_scraper_health()
        
        # BigQuery health
        components["bigquery"] = await self._check_bigquery_health()
        
        # External dependencies
        components["external"] = await self._check_external_dependencies()
        
        # Overall status
        overall_healthy = all(
            comp.get("status") == "healthy" 
            for comp in components.values()
        )
        
        health_data.update({
            "status": "healthy" if overall_healthy else "degraded",
            "components": components
        })
        
        return health_data
    
    async def _check_scraper_health(self) -> Dict[str, Any]:
        """Check scraper component health"""
        if not self.scraper_instance:
            return {
                "status": "unavailable",
                "message": "Scraper not initialized"
            }
        
        try:
            # Quick test - check store types availability
            selector_count = len(STORE_SELECTORS)
            
            return {
                "status": "healthy",
                "store_types_available": selector_count,
                "message": f"Scraper ready with {selector_count} store types"
            }
        except Exception as e:
            logger.error(f"Scraper health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Scraper error: {str(e)}"
            }
    
    async def _check_bigquery_health(self) -> Dict[str, Any]:
        """Check BigQuery component health"""
        if not self.bq_loader_instance:
            return {
                "status": "unavailable",
                "message": "BigQuery loader not initialized"
            }
        
        try:
            # Test BigQuery connection
            client = bigquery.Client()
            
            # Try to access the dataset
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            dataset_id = os.getenv("BIGQUERY_DATASET_ID", "s_kaupat")
            
            if not project_id:
                return {
                    "status": "misconfigured",
                    "message": "GOOGLE_CLOUD_PROJECT not set"
                }
            
            # Quick query to test connection
            query = f"SELECT COUNT(*) as count FROM `{project_id}.{dataset_id}.stores` LIMIT 1"
            
            start_time = time.time()
            job = client.query(query)
            result = list(job.result())
            duration_ms = (time.time() - start_time) * 1000
            
            store_count = result[0].count if result else 0
            
            return {
                "status": "healthy",
                "store_count": store_count,
                "query_duration_ms": round(duration_ms, 2),
                "dataset": f"{project_id}.{dataset_id}",
                "message": f"BigQuery healthy with {store_count} stores"
            }
            
        except Exception as e:
            logger.error(f"BigQuery health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"BigQuery error: {str(e)}"
            }
    
    async def _check_external_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies (S-kaupat.fi)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = time.time()
                response = await client.get("https://www.s-kaupat.fi")
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "s_kaupat_response_time_ms": round(duration_ms, 2),
                        "message": "S-kaupat.fi accessible"
                    }
                else:
                    return {
                        "status": "degraded",
                        "status_code": response.status_code,
                        "message": f"S-kaupat.fi returned {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"External dependency check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"S-kaupat.fi unreachable: {str(e)}"
            }
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Readiness check for Kubernetes/Cloud Run"""
        components = {
            "scraper": await self._check_scraper_health(),
            "bigquery": await self._check_bigquery_health()
        }
        
        # Service is ready if core components are available
        ready = (
            components["scraper"].get("status") in ["healthy", "degraded"] and
            components["bigquery"].get("status") in ["healthy", "unavailable"]  # BigQuery optional
        )
        
        return {
            "ready": ready,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "components": components
        }
    
    async def check_liveness(self) -> Dict[str, Any]:
        """Liveness check for Kubernetes/Cloud Run"""
        # Simple check - if we can respond, we're alive
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds()
        }
