"""Command-line interface for the Ruokahinta scraper."""

import asyncio
import json
import sys
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

import click

from .main import run_scrape, run_product_scrape, scrape_single_product


def setup_logging(verbose: bool):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
def cli():
    """Ruokahinta scraper - Extract store data from Finnish grocery services"""
    pass


@cli.command()
@click.option(
    "--browser",
    is_flag=True,
    help="Force browser-based scraping instead of trying API first."
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (JSON format). Default: scraped_stores.json"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(['json', 'csv']),
    default='json',
    help="Output format (json or csv)."
)
@click.option(
    "--limit",
    type=int,
    help="Limit the number of stores to scrape (for testing)."
)
@click.option(
    "--store-types",
    help="Comma-separated list of store types to scrape (e.g., Prisma,S-market)."
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging."
)
@click.option(
    "--quiet",
    "-q", 
    is_flag=True,
    help="Suppress all output except errors."
)
def scrape(browser: bool, output: Optional[str], output_format: str, limit: Optional[int], 
          store_types: Optional[str], verbose: bool, quiet: bool):
    """Scrape Finnish grocery store data."""
    
    setup_logging(verbose)
    
    # Set default output file if not provided
    if not output:
        output = f"scraped_stores.{output_format}"
    
    async def main():
        try:
            if not quiet:
                click.echo("🚀 Starting Ruokahinta scraper...")
            
            stores = await run_scrape(use_browser=browser)
            
            if not stores:
                click.echo("❌ No stores found. This might indicate a problem with the site.", err=True)
                sys.exit(1)
            
            # Filter by store types if specified
            if store_types:
                requested_types = [t.strip() for t in store_types.split(',')]
                original_count = len(stores)
                stores = [s for s in stores if s['store_type'] in requested_types]
                if not quiet:
                    click.echo(f"📍 Filtered to {len(stores)} stores of types: {', '.join(requested_types)} (was {original_count})")
            
            # Apply limit if specified
            if limit:
                original_count = len(stores)
                stores = stores[:limit]
                if not quiet:
                    click.echo(f"📊 Limited to {len(stores)} stores (was {original_count})")
            
            # Save results
            output_path = Path(output)
            
            if output_format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(stores, f, indent=2, ensure_ascii=False)
            elif output_format == 'csv':
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if stores:
                        writer = csv.DictWriter(f, fieldnames=stores[0].keys())
                        writer.writeheader()
                        writer.writerows(stores)
            
            if not quiet:
                click.echo(f"✅ Successfully scraped {len(stores)} stores!")
                click.echo(f"💾 Results saved to: {output_path}")
                
                # Show summary
                store_types_summary = {}
                for store in stores:
                    store_type = store['store_type']
                    store_types_summary[store_type] = store_types_summary.get(store_type, 0) + 1
                
                click.echo("\n📊 Summary by store type:")
                for store_type, count in sorted(store_types_summary.items()):
                    click.echo(f"  • {store_type}: {count} stores")
                
        except KeyboardInterrupt:
            click.echo("\n⚠️ Scraping interrupted by user", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error during scraping: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(main())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def validate(file_path: str):
    """Validate scraped data file structure."""
    try:
        click.echo(f"🔍 Validating {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        
        if not isinstance(stores, list):
            click.echo("❌ File should contain a list of stores", err=True)
            return
        
        click.echo(f"📊 Found {len(stores)} stores")
        
        # Validate structure
        required_fields = [
            'name', 'address', 'city', 'postal_code', 'phone', 
            'hours', 'services', 'latitude', 'longitude', 
            'store_type', 'scraped_at', 'source'
        ]
        
        errors = []
        for i, store in enumerate(stores):
            for field in required_fields:
                if field not in store:
                    errors.append(f"Store {i}: Missing field '{field}'")
        
        if errors:
            click.echo(f"❌ Found {len(errors)} validation errors:")
            for error in errors[:10]:  # Show first 10 errors
                click.echo(f"  • {error}")
            if len(errors) > 10:
                click.echo(f"  ... and {len(errors) - 10} more errors")
        else:
            click.echo("✅ All stores have valid structure")
        
        # Show summary
        store_types = {}
        sources = {}
        
        for store in stores:
            store_type = store.get('store_type', 'Unknown')
            source = store.get('source', 'Unknown')
            
            store_types[store_type] = store_types.get(store_type, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        click.echo("\n📊 Store types:")
        for store_type, count in sorted(store_types.items()):
            click.echo(f"  • {store_type}: {count}")
        
        click.echo("\n📡 Data sources:")
        for source, count in sorted(sources.items()):
            click.echo(f"  • {source}: {count}")
            
    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON file: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error validating file: {e}", err=True)


@cli.command()
def version():
    """Show version information."""
    click.echo("Ruokahinta v1.0.0")
    click.echo("🛒 Scraper for Finnish grocery store data")


@cli.command()
@click.argument('product_url')
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (JSON format). Default: product_data.json"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging."
)
@click.option(
    "--quiet",
    "-q", 
    is_flag=True,
    help="Suppress all output except errors."
)
def scrape_product(product_url: str, output: Optional[str], verbose: bool, quiet: bool):
    """Scrape product data from a single Finnish grocery store product URL."""
    
    setup_logging(verbose)
    
    # Set default output file if not provided
    if not output:
        output = "product_data.json"
    
    async def main():
        try:
            if not quiet:
                click.echo("🔍 Scraping product data...")
            
            # Scrape the product data
            product_data = await scrape_single_product(product_url)
            
            if not product_data:
                click.echo("❌ No product data found. This might indicate a problem with the URL or the site.", err=True)
                sys.exit(1)
            
            # Save results
            output_path = Path(output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2, ensure_ascii=False)
            
            if not quiet:
                click.echo(f"✅ Successfully scraped product data!")
                click.echo(f"💾 Results saved to: {output_path}")
                
        except KeyboardInterrupt:
            click.echo("\n⚠️ Scraping interrupted by user", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error during product scraping: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(main())


@cli.command()
@click.argument('urls_file', type=click.Path(exists=True))
@click.option(
    "--output",
    "-o", 
    type=click.Path(),
    help="Output file path (JSON format). Default: products_data.json"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging."
)
@click.option(
    "--quiet",
    "-q", 
    is_flag=True,
    help="Suppress all output except errors."
)
def scrape_products(urls_file: str, output: Optional[str], verbose: bool, quiet: bool):
    """Scrape product data from multiple Finnish grocery store product URLs.
    
    URLS_FILE should contain one product URL per line.
    """
    
    setup_logging(verbose)
    
    # Set default output file if not provided
    if not output:
        output = "products_data.json"
    
    async def main():
        try:
            if not quiet:
                click.echo("🔍 Reading product URLs...")
                
            # Read URLs from file
            with open(urls_file, 'r', encoding='utf-8') as f:
                product_urls = [line.strip() for line in f if line.strip()]
            
            if not product_urls:
                click.echo("❌ No URLs found in the file", err=True)
                sys.exit(1)
                
            if not quiet:
                click.echo(f"📦 Found {len(product_urls)} product URLs to scrape")
                click.echo("🔍 Scraping product data...")
            
            # Scrape the product data
            products_data = await run_product_scrape(product_urls)
            
            if not products_data:
                click.echo("❌ No product data found. This might indicate a problem with the URLs or the site.", err=True)
                sys.exit(1)
            
            # Save results
            output_path = Path(output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(products_data, f, indent=2, ensure_ascii=False)
            
            if not quiet:
                click.echo(f"✅ Successfully scraped {len(products_data)} products!")
                click.echo(f"💾 Results saved to: {output_path}")
                
        except KeyboardInterrupt:
            click.echo("\n⚠️ Scraping interrupted by user", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error during product scraping: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(main())


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (JSON format). Default: all_products_YYYYMMDD_HHMMSS.json"
)
@click.option(
    "--batch-size",
    type=int,
    default=50,
    help="Number of products to scrape per batch (default: 50)"
)
@click.option(
    "--discover-first",
    is_flag=True,
    help="First discover all product URLs, then scrape them"
)
@click.option(
    "--urls-file",
    type=click.Path(),
    default="all_product_urls.json",
    help="File containing product URLs to scrape"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging."
)
def scrape_all_products(output: Optional[str], batch_size: int, discover_first: bool, urls_file: str, verbose: bool):
    """Scrape ALL products from Finnish grocery stores - comprehensive bulk operation.
    
    This command will either:
    1. Discover all product URLs and then scrape them (with --discover-first)
    2. Scrape products from an existing URLs file
    """
    
    setup_logging(verbose)
    
    # Set default output file if not provided
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"all_products_{timestamp}.json"
    
    async def main():
        try:
            if discover_first:
                click.echo("🔍 Phase 1: Discovering all product URLs...")
                
                # Import discovery script functionality
                import subprocess
                import sys
                
                # Run discovery script
                result = subprocess.run([sys.executable, "discover_all_products.py"], 
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    click.echo(f"❌ Discovery failed: {result.stderr}", err=True)
                    sys.exit(1)
                
                click.echo(f"✅ Discovery completed! URLs saved to {urls_file}")
            
            # Check if URLs file exists
            if not Path(urls_file).exists():
                click.echo(f"❌ URLs file '{urls_file}' not found!", err=True)
                click.echo("Run with --discover-first to find all product URLs first", err=True)
                sys.exit(1)
            
            click.echo("🔍 Phase 2: Loading product URLs...")
            
            # Load URLs
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls = json.load(f)
            
            if not urls:
                click.echo("❌ No URLs found in file!", err=True)
                sys.exit(1)
            
            click.echo(f"📦 Found {len(urls)} product URLs to scrape")
            click.echo(f"🔄 Processing in batches of {batch_size}")
            click.echo("🚀 Starting bulk scraping...")
            
            # Scrape in batches
            all_products = []
            total_batches = (len(urls) + batch_size - 1) // batch_size
            
            for i in range(0, len(urls), batch_size):
                batch_num = (i // batch_size) + 1
                batch_urls = urls[i:i + batch_size]
                
                click.echo(f"⚡ Processing batch {batch_num}/{total_batches} ({len(batch_urls)} products)...")
                
                try:
                    batch_products = await run_product_scrape(batch_urls)
                    
                    if batch_products:
                        all_products.extend(batch_products)
                        click.echo(f"✅ Batch {batch_num} completed: {len(batch_products)} products scraped")
                    else:
                        click.echo(f"⚠️ Batch {batch_num}: No products scraped")
                    
                    # Save intermediate results every 5 batches
                    if batch_num % 5 == 0:
                        intermediate_file = f"intermediate_products_batch_{batch_num}.json"
                        with open(intermediate_file, 'w', encoding='utf-8') as f:
                            json.dump(all_products, f, indent=2, ensure_ascii=False)
                        click.echo(f"💾 Intermediate results saved: {intermediate_file}")
                    
                    # Brief pause between batches
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    click.echo(f"❌ Error in batch {batch_num}: {e}", err=True)
                    continue
            
            # Save final results
            output_path = Path(output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, indent=2, ensure_ascii=False)
            
            # Show final statistics
            successful = len([p for p in all_products if p.get('name')])
            failed = len(all_products) - successful
            success_rate = (successful / len(all_products) * 100) if all_products else 0
            
            click.echo("\n🎉 BULK SCRAPING COMPLETED!")
            click.echo(f"📊 Total products processed: {len(all_products)}")
            click.echo(f"✅ Successful: {successful}")
            click.echo(f"❌ Failed: {failed}")
            click.echo(f"📈 Success rate: {success_rate:.1f}%")
            click.echo(f"💾 Results saved to: {output_path}")
            
        except KeyboardInterrupt:
            click.echo("\n⚠️ Bulk scraping interrupted by user", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error during bulk scraping: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(main())


if __name__ == "__main__":
    cli()
