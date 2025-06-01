#!/usr/bin/env python3
"""
K-ruoka BigQuery loader for anti-bot scraped data.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime
import time

from loader.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KRuokaProductBigQueryLoader:
    """BigQuery loader specifically for K-ruoka product data."""
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize the loader."""
        self.project_id = project_id or Config.get_project_id()
        if not self.project_id:
            raise ValueError("Project ID must be specified")
        
        self.dataset_id = Config.K_RUOKA_DATASET_ID
        self.table_id = Config.K_RUOKA_TABLE_ID
        
        # Initialize BigQuery client
        self.client = bigquery.Client(project=self.project_id)
        
        # Define schema for K-ruoka products
        self.schema = [
            bigquery.SchemaField("name", "STRING", mode="REQUIRED", description="Product name"),
            bigquery.SchemaField("price", "STRING", mode="NULLABLE", description="Product price as displayed"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE", description="Product description"),
            bigquery.SchemaField("url", "STRING", mode="REQUIRED", description="Product URL"),
            bigquery.SchemaField("scraped_at", "TIMESTAMP", mode="REQUIRED", description="When the product was scraped"),
            bigquery.SchemaField("source", "STRING", mode="REQUIRED", description="Source of the data (k-ruoka)"),
            bigquery.SchemaField("price_numeric", "FLOAT64", mode="NULLABLE", description="Extracted numeric price"),
            bigquery.SchemaField("category", "STRING", mode="NULLABLE", description="Product category"),
            bigquery.SchemaField("brand", "STRING", mode="NULLABLE", description="Product brand"),
            bigquery.SchemaField("unit", "STRING", mode="NULLABLE", description="Product unit (kg, l, pcs)"),
        ]
    
    def ensure_dataset_exists(self):
        """Create dataset if it doesn't exist."""
        dataset_ref = self.client.dataset(self.dataset_id)
        
        try:
            dataset = self.client.get_dataset(dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = Config.DEFAULT_LOCATION
            dataset.description = "K-ruoka product data scraped with anti-bot techniques"
            
            dataset = self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {self.dataset_id}")
        
        return dataset
    
    def ensure_table_exists(self):
        """Create table if it doesn't exist."""
        self.ensure_dataset_exists()
        
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        try:
            table = self.client.get_table(table_ref)
            logger.info(f"Table {self.table_id} already exists")
        except NotFound:
            table = bigquery.Table(table_ref, schema=self.schema)
            table.description = "K-ruoka product data with anti-bot protection bypass"
            
            table = self.client.create_table(table, timeout=30)
            logger.info(f"Created table {self.table_id}")
        
        return table
    
    def extract_price_numeric(self, price_str: str) -> Optional[float]:
        """Extract numeric price from price string."""
        if not price_str:
            return None
        
        try:
            # Remove common Finnish price formatting
            price_clean = price_str.replace('€', '').replace(',', '.').strip()
            
            # Extract first number found
            import re
            price_match = re.search(r'(\d+\.?\d*)', price_clean)
            if price_match:
                return float(price_match.group(1))
        except:
            pass
        
        return None
    
    def extract_category_from_url(self, url: str) -> Optional[str]:
        """Extract category from product URL."""
        try:
            # K-ruoka URLs often contain category information
            if '/kategoria/' in url or '/category/' in url:
                parts = url.split('/')
                for i, part in enumerate(parts):
                    if part in ['kategoria', 'category'] and i + 1 < len(parts):
                        return parts[i + 1].replace('-', ' ').title()
        except:
            pass
        
        return None
    
    def transform_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw product data for BigQuery."""
        # Convert scraped_at to timestamp if it's a Unix timestamp
        scraped_at = product.get('scraped_at')
        if isinstance(scraped_at, (int, float)):
            scraped_at = datetime.fromtimestamp(scraped_at)
        elif isinstance(scraped_at, str):
            try:
                scraped_at = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
            except:
                scraped_at = datetime.now()
        else:
            scraped_at = datetime.now()
        
        # Extract numeric price
        price_numeric = self.extract_price_numeric(product.get('price', ''))
        
        # Extract category from URL
        category = self.extract_category_from_url(product.get('url', ''))
        
        transformed = {
            'name': product.get('name', '').strip(),
            'price': product.get('price', '').strip() if product.get('price') else None,
            'description': product.get('description', '').strip() if product.get('description') else None,
            'url': product.get('url', ''),
            'scraped_at': scraped_at,
            'source': product.get('source', 'k-ruoka'),
            'price_numeric': price_numeric,
            'category': category,
            'brand': None,  # Can be extracted from product name if needed
            'unit': None,   # Can be extracted from price or description if needed
        }
        
        return transformed
    
    def load_products(self, products: List[Dict[str, Any]], batch_size: int = 1000) -> bool:
        """Load products to BigQuery in batches."""
        if not products:
            logger.warning("No products to load")
            return True
        
        self.ensure_table_exists()
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        # Transform all products
        transformed_products = []
        for product in products:
            try:
                transformed = self.transform_product_data(product)
                if transformed['name']:  # Only include products with names
                    transformed_products.append(transformed)
            except Exception as e:
                logger.warning(f"Failed to transform product {product.get('url', 'unknown')}: {e}")
                continue
        
        if not transformed_products:
            logger.warning("No valid products to load after transformation")
            return True
        
        logger.info(f"Loading {len(transformed_products)} products to BigQuery")
        
        # Load in batches
        total_loaded = 0
        for i in range(0, len(transformed_products), batch_size):
            batch = transformed_products[i:i + batch_size]
            
            try:
                job_config = bigquery.LoadJobConfig(
                    schema=self.schema,
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                )
                
                job = self.client.load_table_from_json(
                    batch, table_ref, job_config=job_config
                )
                
                job.result()  # Wait for the job to complete
                
                if job.errors:
                    logger.error(f"Batch {i//batch_size + 1} errors: {job.errors}")
                    return False
                else:
                    total_loaded += len(batch)
                    logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} products")
                
            except Exception as e:
                logger.error(f"Failed to load batch {i//batch_size + 1}: {e}")
                return False
        
        logger.info(f"Successfully loaded {total_loaded} products to BigQuery")
        return True
    
    def load_from_file(self, file_path: str) -> bool:
        """Load products from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            if not isinstance(products, list):
                logger.error("JSON file must contain a list of products")
                return False
            
            return self.load_products(products)
            
        except Exception as e:
            logger.error(f"Failed to load from file {file_path}: {e}")
            return False
    
    def get_product_count(self) -> int:
        """Get count of products in the table."""
        try:
            query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            """
            
            result = self.client.query(query).result()
            return list(result)[0]['count']
            
        except Exception as e:
            logger.error(f"Failed to get product count: {e}")
            return 0
    
    def get_latest_products(self, limit: int = 10) -> List[Dict]:
        """Get the most recently scraped products."""
        try:
            query = f"""
            SELECT name, price, url, scraped_at, category
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            ORDER BY scraped_at DESC
            LIMIT {limit}
            """
            
            result = self.client.query(query).result()
            return [dict(row) for row in result]
            
        except Exception as e:
            logger.error(f"Failed to get latest products: {e}")
            return []
    
    def get_price_statistics(self) -> Dict[str, Any]:
        """Get price statistics for K-ruoka products."""
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_products,
                COUNT(price_numeric) as products_with_price,
                AVG(price_numeric) as avg_price,
                MIN(price_numeric) as min_price,
                MAX(price_numeric) as max_price,
                STDDEV(price_numeric) as price_stddev
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE price_numeric IS NOT NULL AND price_numeric > 0
            """
            
            result = self.client.query(query).result()
            return dict(list(result)[0])
            
        except Exception as e:
            logger.error(f"Failed to get price statistics: {e}")
            return {}

def main():
    """Example usage of the K-ruoka BigQuery loader."""
    # Example: Load from scraped files
    loader = KRuokaProductBigQueryLoader()
    
    # Check if we have any scraped files to load
    import glob
    import os
    
    json_files = glob.glob('k_ruoka_*.json')
    if json_files:
        logger.info(f"Found {len(json_files)} K-ruoka JSON files to load")
        
        for file_path in json_files:
            logger.info(f"Loading {file_path}...")
            if loader.load_from_file(file_path):
                logger.info(f"Successfully loaded {file_path}")
            else:
                logger.error(f"Failed to load {file_path}")
    else:
        logger.info("No K-ruoka JSON files found to load")
    
    # Show statistics
    count = loader.get_product_count()
    logger.info(f"Total K-ruoka products in BigQuery: {count}")
    
    if count > 0:
        latest = loader.get_latest_products(5)
        logger.info("Latest products:")
        for product in latest:
            logger.info(f"  {product['name']} - {product['price']} - {product['scraped_at']}")
        
        stats = loader.get_price_statistics()
        if stats:
            logger.info(f"Price statistics: {stats}")

if __name__ == "__main__":
    main()
