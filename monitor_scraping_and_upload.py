#!/usr/bin/env python3
"""
Monitor scraping progress and automatically upload new batches to BigQuery.
"""

import os
import json
import time
import glob
from datetime import datetime
from loader.main import ProductBigQueryLoader

def check_progress():
    """Check the current scraping progress."""
    # Count total URLs
    try:
        with open('quick_product_urls.json') as f:
            total_urls = len(json.load(f))
    except FileNotFoundError:
        total_urls = 4126  # Known count
    
    # Count products in all batch files
    total_products = 0
    batch_files = glob.glob('intermediate_products_batch_*.json')
    batch_files.extend(glob.glob('additional_products_*.json'))
    
    latest_batch = 0
    
    for file in batch_files:
        try:
            with open(file) as f:
                data = json.load(f)
                count = len(data)
                total_products += count
                
                # Extract batch number from filename
                if 'batch_' in file:
                    try:
                        batch_num = int(file.split('batch_')[1].split('.')[0])
                        latest_batch = max(latest_batch, batch_num)
                    except ValueError:
                        pass
                
                print(f"  {file}: {count} products")
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    
    progress_pct = (total_products / total_urls) * 100 if total_urls > 0 else 0
    
    print(f"\n📊 SCRAPING PROGRESS:")
    print(f"  Total URLs: {total_urls}")
    print(f"  Products scraped: {total_products}")
    print(f"  Progress: {progress_pct:.1f}%")
    print(f"  Latest batch: {latest_batch}")
    
    return total_products, latest_batch

def check_bigquery_status():
    """Check current BigQuery status."""
    try:
        loader = ProductBigQueryLoader(project_id='ruokahinta-scraper-1748695687')
        
        query = '''
        SELECT 
            COUNT(*) as total_products,
            COUNT(DISTINCT url) as unique_urls,
            MAX(scraped_at) as last_upload
        FROM `{}.{}.{}`
        '''.format(loader.project_id, loader.dataset_id, loader.table_id)
        
        result = loader.client.query(query).result()
        for row in result:
            print(f"\n💾 BIGQUERY STATUS:")
            print(f"  Products in BigQuery: {row.total_products}")
            print(f"  Unique URLs: {row.unique_urls}")
            print(f"  Last upload: {row.last_upload}")
            return row.total_products
            
    except Exception as e:
        print(f"\n❌ BigQuery check failed: {e}")
        return 0

def upload_new_batches():
    """Upload any new batch files to BigQuery."""
    # Find all batch files
    batch_files = glob.glob('intermediate_products_batch_*.json')
    batch_files.extend(glob.glob('additional_products_*.json'))
    
    # Check what's already been uploaded by looking at timestamps
    loader = ProductBigQueryLoader(project_id='ruokahinta-scraper-1748695687')
    
    for file in batch_files:
        file_time = os.path.getmtime(file)
        file_datetime = datetime.fromtimestamp(file_time)
        
        # Check if file was modified in the last hour (likely new)
        now = datetime.now()
        time_diff = (now - file_datetime).total_seconds()
        
        if time_diff < 3600:  # Less than 1 hour old
            try:
                with open(file) as f:
                    data = json.load(f)
                
                if data:  # Only upload if there's data
                    print(f"\n⬆️  Uploading {file} ({len(data)} products) to BigQuery...")
                    job = loader.load_products(data, create_if_needed=True)
                    print(f"  ✅ Upload successful!")
                    
            except Exception as e:
                print(f"  ❌ Upload failed for {file}: {e}")

def main():
    """Main monitoring loop."""
    print("🔍 S-kaupat Scraping & Upload Monitor")
    print("=" * 50)
    
    while True:
        try:
            # Check progress
            total_scraped, latest_batch = check_progress()
            bq_count = check_bigquery_status()
            
            # Upload new batches if needed
            if total_scraped > bq_count:
                print(f"\n🆕 New data detected ({total_scraped - bq_count} new products)")
                upload_new_batches()
            
            # Check if scraping is complete
            if total_scraped >= 4000:  # Close to completion
                print(f"\n🎉 Scraping appears to be nearly complete!")
                print(f"   Consider running final upload and verification.")
            
            print(f"\n⏰ Next check in 60 seconds... (Ctrl+C to stop)")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
