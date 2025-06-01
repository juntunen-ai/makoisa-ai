#!/usr/bin/env python3
"""Test scraper and save results to JSON."""

import asyncio
import json
from scraper.main import run_scrape

async def main():
    """Run scraper and save results."""
    print("Starting S-kaupat scraper...")
    stores = await run_scrape(use_browser=True)
    
    print(f"\nSuccessfully scraped {len(stores)} stores!")
    
    # Save to JSON file
    with open('scraped_stores.json', 'w', encoding='utf-8') as f:
        json.dump(stores, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to scraped_stores.json")
    
    # Show summary by store type
    store_types = {}
    for store in stores:
        store_type = store['store_type']
        if store_type not in store_types:
            store_types[store_type] = []
        store_types[store_type].append(store)
    
    print(f"\nSummary by store type:")
    for store_type, type_stores in store_types.items():
        print(f"  {store_type}: {len(type_stores)} stores")
    
    # Show first few stores from each type
    print(f"\nSample stores:")
    for store_type, type_stores in store_types.items():
        print(f"\n{store_type}:")
        for store in type_stores[:2]:  # Show first 2 stores
            print(f"  - {store['name']}")
            print(f"    {store['address']}")
            if store['hours']:
                print(f"    Hours: {store['hours']}")

if __name__ == "__main__":
    asyncio.run(main())
