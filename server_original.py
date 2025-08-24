"""
FastAPI web server for Makoisa AI
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
from fastapi.middleware.base import BaseHTTPMiddleware
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    global scraper, bq_loader
    
    # Startup
    logger.info("Starting Makoisa AI API...")
    
    # Initialize scraper
    scraper = SKaupatScraper()
    
    # Initialize BigQuery loader if credentials are available
    try:
        config = Config()
        if config.project_id and config.dataset_id:
            bq_loader = BigQueryLoader(config)
            logger.info("BigQuery loader initialized")
        else:
            logger.warning("BigQuery credentials not found, loader disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize BigQuery loader: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Makoisa AI API...")

app = FastAPI(
    title="Makoisa AI API",
    description="REST API for scraping S-kaupat.fi store data and loading to BigQuery",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Makoisa AI API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bigquery_enabled": bq_loader is not None
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "scraper_ready": scraper is not None,
        "bigquery_ready": bq_loader is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stores", response_model=List[Dict[str, Any]])
async def scrape_stores(
    store_type: Optional[str] = Query(None, description="Filter by store type"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Scrape stores from S-kaupat.fi"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    try:
        logger.info(f"Starting scrape request - store_type: {store_type}, limit: {limit}")
        
        # Run scraping
        stores = await scraper.scrape_all_stores()
        
        # Apply filters
        if store_type:
            stores = [s for s in stores if s.get('store_type', '').lower() == store_type.lower()]
        
        if limit:
            stores = stores[:limit]
        
        logger.info(f"Scraping completed - found {len(stores)} stores")
        
        return stores
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
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
    
    try:
        logger.info(f"Starting scrape-and-load - store_type: {store_type}, write_mode: {write_mode}")
        
        # Scrape stores
        stores = await scraper.scrape_all_stores()
        
        # Apply filter if specified
        if store_type:
            stores = [s for s in stores if s.get('store_type', '').lower() == store_type.lower()]
        
        # Load to BigQuery
        result = bq_loader.load_stores(stores, write_mode=write_mode)
        
        logger.info(f"Load completed - processed {len(stores)} stores")
        
        return {
            "status": "success",
            "stores_processed": len(stores),
            "bigquery_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Load to BigQuery failed: {e}")
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
    
    try:
        # Build filters
        filters = {}
        if store_type:
            filters['store_type'] = store_type
        if city:
            filters['city'] = city
        
        # Query BigQuery
        results = bq_loader.query_stores(filters=filters, limit=limit)
        
        return {
            "status": "success",
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"BigQuery query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/bigquery/info")
async def bigquery_info():
    """Get BigQuery dataset and table information"""
    if not bq_loader:
        raise HTTPException(status_code=400, detail="BigQuery loader not available")
    
    try:
        info = bq_loader.get_table_info()
        return {
            "status": "success",
            "info": info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get BigQuery info: {e}")
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
        "total_types": 7
    }

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
