#!/usr/bin/env python3
"""
End-to-end integration script for S-kaupat scraper.
Scrapes stores and loads them directly to BigQuery.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from scraper.main import run_scrape
from loader.main import BigQueryLoader
from loader.config import Config


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


async def scrape_and_load(
    project_id: Optional[str] = None,
    dataset_id: str = "s_kaupat",
    table_id: str = "stores",
    credentials_path: Optional[str] = None,
    store_types: Optional[List[str]] = None,
    limit: Optional[int] = None,
    browser_type: str = "headless",
    write_mode: str = "append",
    save_backup: bool = True,
    verbose: bool = False,
) -> None:
    """Scrape stores and load them to BigQuery.
    
    Args:
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        credentials_path: Path to service account JSON file
        store_types: List of store types to scrape
        limit: Maximum number of stores to scrape
        browser_type: Browser type for scraping (headless/visible)
        write_mode: BigQuery write mode (append/truncate/empty)
        save_backup: Whether to save a local JSON backup
        verbose: Enable verbose logging
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    # Phase 1: Scrape stores
    logger.info("🔍 Starting store scraping...")
    try:
        # Use the async run_scrape function
        use_browser = browser_type == "visible" or browser_type == "browser"
        stores = await run_scrape(use_browser=use_browser)
        
        if not stores:
            logger.error("No stores found during scraping")
            return
        
        # Filter by store types if specified
        if store_types:
            original_count = len(stores)
            stores = [s for s in stores if s.get('store_type') in store_types]
            logger.info(f"Filtered to {len(stores)} stores of types: {', '.join(store_types)} (was {original_count})")
        
        # Apply limit if specified
        if limit:
            original_count = len(stores)
            stores = stores[:limit]
            logger.info(f"Limited to {len(stores)} stores (was {original_count})")
        
        logger.info(f"✓ Successfully scraped {len(stores)} stores")
        
        # Save backup if requested
        if save_backup:
            backup_file = f"scraped_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(stores, f, indent=2, default=str)
            logger.info(f"💾 Backup saved to {backup_file}")
        
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        raise
    
    # Phase 2: Load to BigQuery
    logger.info("📊 Loading data to BigQuery...")
    try:
        # Map write mode
        mode_mapping = {
            'append': 'WRITE_APPEND',
            'truncate': 'WRITE_TRUNCATE',
            'empty': 'WRITE_EMPTY',
        }
        write_disposition = mode_mapping.get(write_mode, 'WRITE_APPEND')
        
        loader = BigQueryLoader(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            credentials_path=credentials_path,
        )
        
        job = loader.load_stores(stores, write_disposition=write_disposition)
        
        logger.info(f"✓ Successfully loaded {job.output_rows} rows to BigQuery")
        logger.info(f"📍 Table: {loader.project_id}.{dataset_id}.{table_id}")
        logger.info(f"🆔 Job ID: {job.job_id}")
        
        # Show table stats
        try:
            info = loader.get_table_info()
            logger.info(f"📈 Total rows in table: {info['num_rows']:,}")
            logger.info(f"💽 Table size: {info['num_bytes']:,} bytes")
        except Exception as e:
            logger.warning(f"Could not get table info: {e}")
        
    except Exception as e:
        logger.error(f"❌ BigQuery loading failed: {e}")
        raise


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="End-to-end S-kaupat scraper with BigQuery loading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all stores and load to BigQuery
  python integration.py --project-id my-project

  # Scrape only Prisma stores with visible browser
  python integration.py --project-id my-project --store-types prisma --browser visible

  # Truncate table and load fresh data
  python integration.py --project-id my-project --write-mode truncate

  # Load to custom dataset/table
  python integration.py --project-id my-project --dataset custom_data --table my_stores
        """,
    )
    
    # Google Cloud arguments
    parser.add_argument(
        "--project-id", "-p",
        help="Google Cloud project ID (can also set GOOGLE_CLOUD_PROJECT env var)"
    )
    parser.add_argument(
        "--dataset-id", "-d",
        default="s_kaupat",
        help="BigQuery dataset ID (default: s_kaupat)"
    )
    parser.add_argument(
        "--table-id", "-t",
        default="stores",
        help="BigQuery table ID (default: stores)"
    )
    parser.add_argument(
        "--credentials", "-c",
        help="Path to service account JSON file"
    )
    
    # Scraping arguments
    parser.add_argument(
        "--store-types", "-s",
        help="Comma-separated list of store types to scrape (e.g., prisma,alepa)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of stores to scrape"
    )
    parser.add_argument(
        "--browser",
        choices=["headless", "visible"],
        default="headless",
        help="Browser mode for scraping (default: headless)"
    )
    
    # Loading arguments
    parser.add_argument(
        "--write-mode", "-m",
        choices=["append", "truncate", "empty"],
        default="append",
        help="BigQuery write mode (default: append)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't save local JSON backup"
    )
    
    # General arguments
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Parse store types
    store_types = None
    if args.store_types:
        store_types = [s.strip() for s in args.store_types.split(",")]
    
    # Use environment variables as fallback
    project_id = args.project_id or Config.get_project_id()
    if not project_id:
        print("❌ Error: Project ID required. Use --project-id or set GOOGLE_CLOUD_PROJECT env var")
        sys.exit(1)
    
    try:
        asyncio.run(scrape_and_load(
            project_id=project_id,
            dataset_id=args.dataset_id,
            table_id=args.table_id,
            credentials_path=args.credentials,
            store_types=store_types,
            limit=args.limit,
            browser_type=args.browser,
            write_mode=args.write_mode,
            save_backup=not args.no_backup,
            verbose=args.verbose,
        ))
        
        print("\n🎉 Integration complete! Stores scraped and loaded to BigQuery.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
