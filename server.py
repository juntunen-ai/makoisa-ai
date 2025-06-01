"""
Enhanced FastAPI web server for S-kaupat scraper with observability
Provides REST API endpoints for scraping and BigQuery operations
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
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
    
    # Initialize scraper without browser (lazy initialization)
    # Browser will be initialized only when needed to avoid startup timeout
    scraper = SKaupatScraper(use_browser=True)
    scraper._context_entered = False
    
    # Initialize BigQuery loader if credentials are available
    try:
        if Config.get_project_id() and Config.get_dataset_id():
            bq_loader = BigQueryLoader()
            logger.info("BigQuery loader initialized", extra={
                "project_id": Config.get_project_id(),
                "dataset_id": Config.get_dataset_id()
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
    
    # Cleanup scraper if it was initialized
    if scraper and hasattr(scraper, '_context_entered') and scraper._context_entered:
        try:
            await scraper.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error during scraper cleanup: {e}")


app = FastAPI(
    title="S-kaupat Scraper API",
    description="REST API for scraping S-kaupat.fi store data and loading to BigQuery",
    version="1.0.0",
    lifespan=lifespan
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)


async def ensure_scraper_ready():
    """Ensure scraper is properly initialized before use"""
    global scraper
    
    if not scraper:
        raise HTTPException(status_code=503, detail="Scraper not initialized")
    
    # Check if scraper context is already entered
    if not hasattr(scraper, '_context_entered') or not scraper._context_entered:
        try:
            logger.info("Initializing scraper browser context...")
            await scraper.__aenter__()
            scraper._context_entered = True
            logger.info("Scraper browser context initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize scraper browser: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to initialize scraper: {str(e)}")
    
    return scraper


@app.get("/")
async def root():
    """Basic service information"""
    return {
        "service": "S-kaupat Scraper API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
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
    # Ensure scraper is ready (lazy initialization)
    scraper_instance = await ensure_scraper_ready()
    
    start_time = time.time()
    
    try:
        log_request(logger, "/stores", {
            "store_type": store_type,
            "limit": limit
        })
        
        # Run scraping
        stores = await scraper_instance.scrape_stores()
        
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


@app.post("/products")
async def scrape_products(
    product_urls: List[str],
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Scrape products from S-kaupat.fi URLs"""
    # Ensure scraper is ready (lazy initialization)
    scraper_instance = await ensure_scraper_ready()
    
    start_time = time.time()
    
    try:
        log_request(logger, "/products", {
            "product_count": len(product_urls),
            "urls": product_urls[:3]  # Log first 3 URLs for debugging
        })
        
        # Run product scraping
        products = await scraper_instance.scrape_products(product_urls)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log metrics
        logger.info(f"Scraped {len(products)} products in {duration_ms:.2f}ms")
        metrics_collector.record_scraping(len(products), "products", duration_ms, True)
        
        return {
            "scraped_count": len(products),
            "products": products,
            "duration_ms": round(duration_ms, 2)
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_scraping(0, "products", duration_ms, False)
        log_error(logger, e, {
            "endpoint": "/products",
            "product_urls": product_urls
        })
        raise HTTPException(status_code=500, detail=f"Product scraping failed: {str(e)}")


@app.get("/product")
async def scrape_single_product(
    url: str = Query(..., description="Product URL to scrape"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Scrape a single product from S-kaupat.fi URL"""
    # Ensure scraper is ready (lazy initialization)
    scraper_instance = await ensure_scraper_ready()
    
    start_time = time.time()
    
    try:
        log_request(logger, "/product", {"url": url})
        
        # Run single product scraping
        product = await scraper_instance.scrape_product(url)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if product:
            # Log metrics
            logger.info(f"Scraped product '{product['name']}' in {duration_ms:.2f}ms")
            metrics_collector.record_scraping(1, "product", duration_ms, True)
            return product
        else:
            metrics_collector.record_scraping(0, "product", duration_ms, False)
            raise HTTPException(status_code=404, detail="Product not found or could not be scraped")
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_scraping(0, "product", duration_ms, False)
        log_error(logger, e, {
            "endpoint": "/product",
            "url": url
        })
        raise HTTPException(status_code=500, detail=f"Product scraping failed: {str(e)}")


@app.post("/bigquery/load")
async def load_to_bigquery(
    store_type: Optional[str] = Query(None, description="Filter by store type"),
    write_mode: str = Query("append", description="Write mode: append, truncate, or empty")
):
    """Scrape stores and load them to BigQuery"""
    if not bq_loader:
        raise HTTPException(status_code=400, detail="BigQuery loader not available")
    
    # Ensure scraper is ready (lazy initialization)
    scraper_instance = await ensure_scraper_ready()
    
    start_time = time.time()
    
    try:
        log_request(logger, "/bigquery/load", {
            "store_type": store_type,
            "write_mode": write_mode
        })
        
        # Scrape stores
        stores = await scraper_instance.scrape_stores()
        
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
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
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
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
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
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
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
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
    }


if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
