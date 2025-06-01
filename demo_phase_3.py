#!/usr/bin/env python3
"""
Demo script for S-kaupat scraper Phase 3 (BigQuery loader).
This script demonstrates the BigQuery loader functionality without actually loading to BigQuery.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from scraper.main import run_scrape
from loader.main import BigQueryLoader
from loader.config import Config


def setup_logging():
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def demo_phase_3():
    """Demonstrate Phase 3 BigQuery loader functionality."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🎯 S-kaupat Scraper - Phase 3 Demo: BigQuery Loader")
    print("=" * 60)
    
    # Demo 1: Show BigQuery loader configuration
    print("\n📋 1. BigQuery Loader Configuration")
    print("-" * 40)
    print(f"Default dataset ID: {Config.DEFAULT_DATASET_ID}")
    print(f"Default table ID: {Config.DEFAULT_TABLE_ID}")
    print(f"Default location: {Config.DEFAULT_LOCATION}")
    
    # Try to get project from environment
    project_id = Config.get_project_id()
    if project_id:
        print(f"Detected project ID: {project_id}")
        print(f"Full table ID: {Config.get_full_table_id(project_id)}")
    else:
        print("No project ID found in environment (GOOGLE_CLOUD_PROJECT)")
    
    # Demo 2: Load and validate existing scraped data
    print("\n📊 2. Data Validation Demo")
    print("-" * 40)
    
    scraped_file = Path("scraped_stores.json")
    if scraped_file.exists():
        with open(scraped_file, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        
        print(f"Loaded {len(stores)} stores from {scraped_file}")
        
        # Create a mock BigQuery loader (without actual credentials)
        try:
            # This will fail without proper credentials, but we can still demonstrate data preparation
            print("Creating BigQuery loader instance...")
            print("(Note: This demo doesn't require actual GCP credentials)")
            
            # Demonstrate data preparation without actual BigQuery
            print("\n🔍 Data Structure Analysis:")
            print(f"Total stores: {len(stores)}")
            
            # Analyze store types
            store_types = {}
            for store in stores:
                store_type = store.get('store_type', 'Unknown')
                store_types[store_type] = store_types.get(store_type, 0) + 1
            
            print("Store types distribution:")
            for store_type, count in sorted(store_types.items()):
                print(f"  - {store_type}: {count} stores")
            
            # Show sample data structure
            if stores:
                print(f"\n📄 Sample store data structure:")
                sample_store = stores[0]
                for key, value in sample_store.items():
                    print(f"  {key}: {type(value).__name__} = {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
            
        except Exception as e:
            print(f"Note: Could not create BigQuery client (expected): {e}")
    else:
        print(f"❌ No scraped data found at {scraped_file}")
        print("Run the scraper first: poetry run python -m scraper.cli scrape")
    
    # Demo 3: Show BigQuery schema
    print("\n📋 3. BigQuery Table Schema")
    print("-" * 40)
    
    # Import here to avoid credentials error
    try:
        from google.cloud.bigquery import SchemaField
        from loader.main import BigQueryLoader
        
        schema = BigQueryLoader.TABLE_SCHEMA
        print("BigQuery table schema:")
        for field in schema:
            mode_str = f" ({field.mode})" if field.mode != "NULLABLE" else ""
            desc_str = f" - {field.description}" if field.description else ""
            print(f"  {field.name}: {field.field_type}{mode_str}{desc_str}")
    except ImportError:
        print("BigQuery dependencies not available for schema display")
    
    # Demo 4: CLI Commands Examples
    print("\n🖥️  4. CLI Commands Examples")
    print("-" * 40)
    print("BigQuery Loader CLI commands:")
    print()
    print("# Dry run validation:")
    print("poetry run python -m loader.cli load scraped_stores.json --dry-run")
    print()
    print("# Load to BigQuery (requires GCP setup):")
    print("poetry run python -m loader.cli load scraped_stores.json --project-id your-project")
    print()
    print("# Query stores from BigQuery:")
    print("poetry run python -m loader.cli query --project-id your-project --limit 10")
    print()
    print("# Setup BigQuery dataset and table:")
    print("poetry run python -m loader.cli setup --project-id your-project")
    print()
    print("# Get table information:")
    print("poetry run python -m loader.cli info --project-id your-project")
    
    # Demo 5: Integration Script Examples
    print("\n🔗 5. End-to-End Integration Examples")
    print("-" * 40)
    print("Complete scrape-and-load workflow:")
    print()
    print("# Scrape all stores and load to BigQuery:")
    print("python integration.py --project-id your-project")
    print()
    print("# Scrape only Prisma stores with visible browser:")
    print("python integration.py --project-id your-project --store-types Prisma --browser visible")
    print()
    print("# Truncate table and load fresh data:")
    print("python integration.py --project-id your-project --write-mode truncate")
    print()
    print("# Scrape limited stores for testing:")
    print("python integration.py --project-id your-project --limit 5 --verbose")
    
    # Demo 6: Python API Usage
    print("\n🐍 6. Python API Usage Examples")
    print("-" * 40)
    print("Using the BigQuery loader in Python code:")
    print()
    print("""```python
from loader.main import BigQueryLoader, load_stores_to_bigquery

# Method 1: Using the BigQueryLoader class
loader = BigQueryLoader(
    project_id="your-project",
    dataset_id="s_kaupat", 
    table_id="stores"
)

# Load stores from list
job = loader.load_stores(stores_list)

# Load from file
job = loader.load_from_file("scraped_stores.json")

# Query stores
results = loader.query_stores(limit=10, store_type="Prisma")

# Method 2: Using convenience function
job = load_stores_to_bigquery(
    stores_list,
    project_id="your-project"
)
```""")
    
    print("\n✅ Phase 3 Demo Complete!")
    print("=" * 60)
    print("🎉 BigQuery loader implementation is ready!")
    print()
    print("Next steps:")
    print("1. Set up Google Cloud credentials")
    print("2. Test with actual BigQuery loading")
    print("3. Proceed to Phase 4: Container & Cloud Run")


if __name__ == "__main__":
    asyncio.run(demo_phase_3())
