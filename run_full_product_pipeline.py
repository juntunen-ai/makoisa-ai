#!/usr/bin/env python3
"""
Automated pipeline: discover product URLs, scrape product data, upload to BigQuery.
"""
import subprocess
import sys
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurable paths
DISCOVER_SCRIPT = "discover_all_products.py"
SCRAPE_SCRIPT = "scrape_all_products.py"
LOADER_CLI = "loader/cli.py"

# Output files
URLS_FILE = "all_product_urls.json"
PRODUCTS_FILE = f"all_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def run_discovery():
    logger.info("[1/3] Discovering all product URLs...")
    result = subprocess.run([sys.executable, DISCOVER_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Discovery failed: {result.stderr}")
        sys.exit(1)
    logger.info("Discovery complete.")


def run_scraping():
    logger.info("[2/3] Scraping all product data...")
    # The scrape script should use URLS_FILE and output PRODUCTS_FILE
    result = subprocess.run([
        sys.executable, SCRAPE_SCRIPT,
        '--urls-file', URLS_FILE,
        '--output', PRODUCTS_FILE
    ], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Scraping failed: {result.stderr}")
        sys.exit(1)
    logger.info(f"Scraping complete. Output: {PRODUCTS_FILE}")


def run_upload():
    logger.info("[3/3] Uploading product data to BigQuery...")
    result = subprocess.run([
        sys.executable, LOADER_CLI, 'load-products', PRODUCTS_FILE
    ], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"BigQuery upload failed: {result.stderr}")
        sys.exit(1)
    logger.info(f"BigQuery upload complete.\n{result.stdout}")


def main():
    run_discovery()
    run_scraping()
    run_upload()
    logger.info("✅ Full product scraping pipeline complete!")

if __name__ == "__main__":
    main()
