"""
Enhanced FastAPI web server for S-kaupat scraper with observability
Provides REST API endpoints for scraping and BigQuery operations
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import uvicorn

from scraper.main import SKaupatScraper
from loader.main import BigQueryLoader
from loader.config import Config

# Import observability modules
from observability.logging import setup_logging, log_request, log_scraping_metrics, log_bigquery_operation, log_error
from observability.health import HealthChecker
from observability.metrics import metrics_collector

# Setup structured logging
logger = setup_logging()

# Global instances
scraper = None
bq_loader = None
health_checker = HealthChecker()


class MetricsMiddleware:
    """Middleware to collect request metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = (time.time() - start_time) * 1000
                endpoint = scope["path"]
                status_code = message["status"]
                
                # Record metrics
                metrics_collector.record_request(endpoint, duration_ms, status_code)
                
                # Log request
                log_request(logger, endpoint, {
                    "method": scope["method"],
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2)
                })
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    global scraper, bq_loader, health_checker
    
    # Startup
    logger.info("Starting S-kaupat Scraper API with observability...")
    
    # Initialize scraper
    scraper = SKaupatScraper()
    
    # Initialize BigQuery loader if credentials are available
    try:
        config = Config()
        if config.project_id and config.dataset_id:
            bq_loader = BigQueryLoader(config)
            logger.info("BigQuery loader initialized", extra={
                "project_id": config.project_id,
                "dataset_id": config.dataset_id
            })
        else:
            logger.warning("BigQuery credentials not found, loader disabled")
    except Exception as e:
        log_error(logger, e, {"component": "bigquery_loader_init"})
    
    # Set health checker instances
    health_checker.set_instances(scraper, bq_loader)
    
    logger.info("S-kaupat Scraper API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down S-kaupat Scraper API...")


app = FastAPI(
    title="S-kaupat Scraper API",
    description="REST API for scraping S-kaupat.fi store data and loading to BigQuery",
    version="1.0.0",
    lifespan=lifespan
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)


@app.get("/")
async def root():
    """Basic service information"""
    return {
        "service": "S-kaupat Scraper API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bigquery_enabled": bq_loader is not None,
        "endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed", 
            "readiness": "/health/ready",
            "liveness": "/health/live",
            "metrics": "/metrics",
            "stores": "/stores",
            "bigquery": "/bigquery/*",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    return await health_checker.check_basic_health()


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    return await health_checker.check_detailed_health()


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes/Cloud Run readiness probe"""
    return await health_checker.check_readiness()


@app.get("/health/live")
async def liveness_check():
    """Kubernetes/Cloud Run liveness probe"""
    return await health_checker.check_liveness()


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return metrics_collector.get_all_metrics()


@app.get("/stores", response_model=List[Dict[str, Any]])
async def scrape_stores(
    store_type: Optional[str] = Query(None, description="Filter by store type"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Scrape stores from S-kaupat.fi"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    start_time = time.time()
    
    try:
        log_request(logger, "/stores", {
            "store_type": store_type,
            "limit": limit
        })
        
        # Run scraping
        stores = await scraper.scrape_all_stores()
        
        # Apply filters
        if store_type:
            stores = [s for s in stores if s.get('store_type', '').lower() == store_type.lower()]
        
        if limit:
            stores = stores[:limit]
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log metrics
        log_scraping_metrics(logger, len(stores), store_type, duration_ms)
        metrics_collector.record_scraping(len(stores), store_type, duration_ms, True)
        
        return stores
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_scraping(0, store_type, duration_ms, False)
        log_error(logger, e, {
            "endpoint": "/stores",
            "store_type": store_type,
            "limit": limit
        })
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@app.post("/bigquery/load")
async def load_to_bigquery(
    store_type: Optional[str] = Query(None, description="Filter by store type"),
    write_mode: str = Query("append", description="Write mode: append, truncate, or empty")
):
    """Scrape stores and load them to BigQuery"""
    if not bq_loader:
        raise HTTPException(status_code=400, detail="BigQuery loader not available")
    
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    start_time = time.time()
    
    try:
        log_request(logger, "/bigquery/load", {
            "store_type": store_type,
            "write_mode": write_mode
        })
        
        # Scrape stores
        stores = await scraper.scrape_all_stores()
        
        # Apply filter if specified
        if store_type:
            stores = [s for s in stores if s.get('store_type', '').lower() == store_type.lower()]
        
        # Load to BigQuery
        bq_start_time = time.time()
        result = bq_loader.load_stores(stores, write_mode=write_mode)
        bq_duration_ms = (time.time() - bq_start_time) * 1000
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log metrics
        log_scraping_metrics(logger, len(stores), store_type, duration_ms)
        log_bigquery_operation(logger, "load", len(stores), bq_duration_ms, True)
        metrics_collector.record_scraping(len(stores), store_type, duration_ms, True)
        metrics_collector.record_bigquery_operation("load", len(stores), bq_duration_ms, True)
        
        return {
            "status": "success",
            "stores_processed": len(stores),
            "bigquery_result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_ms": round(duration_ms, 2)
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_bigquery_operation("load", 0, duration_ms, False)
        log_error(logger, e, {
            "endpoint": "/bigquery/load",
            "store_type": store_type,
            "write_mode": write_mode
        })
        raise HTTPException(status_code=500, detail=f"Load failed: {str(e)}")


@app.get("/bigquery/query")
async def query_bigquery(
    store_type: Optional[str] = Query(None, description="Filter by store type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(100, description="Limit number of results")
):
    """Query stores from BigQuery"""
    if not bq_loader:
        raise HTTPException(status_code=400, detail="BigQuery loader not available")
    
    start_time = time.time()
    
    try:
        log_request(logger, "/bigquery/query", {
            "store_type": store_type,
            "city": city,
            "limit": limit
        })
        
        # Build filters
        filters = {}
        if store_type:
            filters['store_type'] = store_type
        if city:
            filters['city'] = city
        
        # Query BigQuery
        results = bq_loader.query_stores(filters=filters, limit=limit)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log metrics
        log_bigquery_operation(logger, "query", len(results), duration_ms, True)
        metrics_collector.record_bigquery_operation("query", len(results), duration_ms, True)
        
        return {
            "status": "success",
            "results": results,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_ms": round(duration_ms, 2)
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_bigquery_operation("query", 0, duration_ms, False)
        log_error(logger, e, {
            "endpoint": "/bigquery/query",
            "filters": {"store_type": store_type, "city": city, "limit": limit}
        })
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/bigquery/info")
async def bigquery_info():
    """Get BigQuery dataset and table information"""
    if not bq_loader:
        raise HTTPException(status_code=400, detail="BigQuery loader not available")
    
    start_time = time.time()
    
    try:
        info = bq_loader.get_table_info()
        
        duration_ms = (time.time() - start_time) * 1000
        log_bigquery_operation(logger, "info", None, duration_ms, True)
        metrics_collector.record_bigquery_operation("info", None, duration_ms, True)
        
        return {
            "status": "success",
            "info": info,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_bigquery_operation("info", None, duration_ms, False)
        log_error(logger, e, {"endpoint": "/bigquery/info"})
        raise HTTPException(status_code=500, detail=f"Info request failed: {str(e)}")


@app.get("/store-types")
async def get_store_types():
    """Get list of available store types"""
    return {
        "store_types": [
            "prisma",
            "s-market", 
            "alepa",
            "sale",
            "food-market-herkku",
            "sokos-herkku",
            "mestarin-herkku"
        ],
        "total_types": 7,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
