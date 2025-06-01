"""Main scraper module for S-kaupat.fi."""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
from dateutil.parser import parse as parse_date

from .selectors import (
    BASE_URL,
    STORES_URL,
    API_BASE_URL,
    STORES_API_ENDPOINT,
    DEFAULT_HEADERS,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS,
    MAX_CONCURRENT_REQUESTS,
    STORE_TYPE_LINKS_SELECTOR,
    STORE_CARD_SELECTOR,
    STORE_NAME_SELECTOR,
    STORE_ADDRESS_SELECTOR,
    STORE_HOURS_SELECTOR,
    PRODUCT_NAME_SELECTOR,
    PRODUCT_PRICE_SELECTOR,
    PRODUCT_DESCRIPTION_SELECTOR,
    PRODUCT_URL_PATTERN,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SKaupatScraper:
    """Main scraper class for S-kaupat.fi."""

    def __init__(self, use_browser: bool = False):
        """Initialize the scraper.
        
        Args:
            use_browser: If True, use Playwright browser. If False, try API first.
        """
        self.use_browser = use_browser
        self.session: Optional[httpx.AsyncClient] = None
        self.browser: Optional[Browser] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def __aenter__(self):
        """Async context manager entry."""
        if self.use_browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
        else:
            self.session = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=30.0,
                follow_redirects=True
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.session:
            await self.session.aclose()

    async def _rate_limit(self):
        """Apply rate limiting with random delay."""
        delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        await asyncio.sleep(delay)

    async def _try_api_approach(self) -> Optional[List[Dict[str, Any]]]:
        """Try to find and use API endpoints."""
        logger.info("Attempting to discover API endpoints...")
        
        try:
            # Try the actual S-kaupat API endpoint
            api_urls = [
                STORES_API_ENDPOINT,
                f"{API_BASE_URL}/store-locator",
                f"{API_BASE_URL}/v1/stores",
                f"{API_BASE_URL}/locations",
            ]
            
            for url in api_urls:
                try:
                    response = await self.session.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"Found API endpoint: {url}")
                            return self._normalize_api_data(data)
                except Exception as e:
                    logger.debug(f"API endpoint {url} failed: {e}")
                    continue
                    
            # Try to find API calls in the main page
            response = await self.session.get(STORES_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for script tags that might contain API calls
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'api' in script.string.lower():
                    # This would need more sophisticated parsing in a real implementation
                    pass
                    
            return None
            
        except Exception as e:
            logger.error(f"API discovery failed: {e}")
            return None

    def _normalize_api_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize API data to our standard format."""
        normalized = []
        
        for item in data:
            store = {
                'name': item.get('name', item.get('title', '')),
                'address': item.get('address', item.get('location', '')),
                'city': item.get('city', ''),
                'postal_code': item.get('postal_code', item.get('zip', '')),
                'phone': item.get('phone', item.get('telephone', '')),
                'hours': item.get('opening_hours', item.get('hours', {})),
                'services': item.get('services', []),
                'latitude': item.get('lat', item.get('latitude')),
                'longitude': item.get('lng', item.get('longitude')),
                'store_type': item.get('type', item.get('category', '')),
                'scraped_at': datetime.now().isoformat(),
                'source': 'api'
            }
            normalized.append(store)
            
        return normalized

    async def _scrape_with_browser(self) -> List[Dict[str, Any]]:
        """Scrape using Playwright browser."""
        logger.info("Using browser-based scraping...")
        
        page = await self.browser.new_page()
        await page.set_extra_http_headers(DEFAULT_HEADERS)
        
        try:
            stores = []
            
            # Navigate to stores page
            await page.goto(STORES_URL, wait_until='networkidle')
            await self._rate_limit()
            
            logger.info("Finding store type links...")
            
            # Get store type links (Prisma, S-market, etc.)
            store_type_elements = await page.query_selector_all(STORE_TYPE_LINKS_SELECTOR)
            logger.info(f"Found {len(store_type_elements)} store types")
            
            # Extract href and text before navigating
            store_types = []
            for element in store_type_elements:
                try:
                    href = await element.get_attribute('href')
                    text = await element.inner_text()
                    if href and text.strip():
                        store_types.append((href, text.strip()))
                except Exception as e:
                    logger.error(f"Error extracting store type info: {e}")
                    continue
            
            # Now navigate to each store type page
            for href, store_type in store_types:
                try:
                    if not href or not store_type.strip():
                        continue
                        
                    # Navigate to store type page
                    full_url = f"{BASE_URL}{href}" if href.startswith('/') else href
                    logger.info(f"Scraping {store_type} stores from {full_url}")
                    
                    await page.goto(full_url, wait_until='networkidle')
                    await self._rate_limit()
                    
                    # Try to find store data on this page
                    store_data = await self._extract_stores_from_page(page, store_type.strip())
                    stores.extend(store_data)
                    
                except Exception as e:
                    logger.error(f"Error processing store type {store_type}: {e}")
                    continue
                    
            return stores
            
        finally:
            await page.close()

    async def _extract_stores_from_page(self, page, store_type: str) -> List[Dict[str, Any]]:
        """Extract store data from a store type page."""
        stores = []
        
        try:
            # Wait for content to load
            await asyncio.sleep(2)
            
            # Use chain-specific selectors based on store type
            chain_selectors = {
                'Prisma': f"a[href*='prisma']:not([href*='/myymalat/'])",
                'S-market': f"a[href*='s-market']:not([href*='/myymalat/'])",
                'Alepa': f"a[href*='alepa']:not([href*='/myymalat/'])",
                'Sale': f"a[href*='sale']:not([href*='/myymalat/'])",
                'Food Market Herkku': f"a[href*='herkku']:not([href*='/myymalat/'])",
                'Sokos Herkku': f"a[href*='herkku']:not([href*='/myymalat/'])",
                'Mestarin Herkku': f"a[href*='herkku']:not([href*='/myymalat/'])",
            }
            
            # Get the appropriate selector
            selector = chain_selectors.get(store_type, STORE_CARD_SELECTOR)
            
            logger.info(f"Using selector for {store_type}: {selector}")
            store_elements = await page.query_selector_all(selector)
            logger.info(f"Found {len(store_elements)} store elements for {store_type}")
            
            if not store_elements:
                # Fallback: try generic selectors
                fallback_selectors = [
                    "a[href*='/myymala/']",
                    "a:has-text('Tilaa verkosta')",
                    "div:has-text('Avoinna')",
                ]
                
                for fallback_selector in fallback_selectors:
                    try:
                        store_elements = await page.query_selector_all(fallback_selector)
                        if store_elements:
                            logger.info(f"Found {len(store_elements)} elements with fallback selector: {fallback_selector}")
                            break
                    except:
                        continue
            
            if not store_elements:
                logger.info(f"No store elements found for {store_type}, trying to extract basic info")
                # Create a placeholder entry
                stores.append({
                    'name': f"{store_type} (Store Type)",
                    'address': "Multiple locations",
                    'city': "",
                    'postal_code': "",
                    'phone': "",
                    'hours': "",
                    'services': [],
                    'latitude': None,
                    'longitude': None,
                    'store_type': store_type,
                    'scraped_at': datetime.now().isoformat(),
                    'source': 'browser'
                })
                return stores
            
            # Extract data from found elements
            for element in store_elements[:20]:  # Limit to first 20 stores
                try:
                    store_data = await self._extract_store_data_from_element(element, store_type)
                    if store_data:
                        stores.append(store_data)
                except Exception as e:
                    logger.error(f"Error extracting store data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting stores from {store_type} page: {e}")
            
        return stores

    async def _extract_store_data_from_element(self, element, store_type: str) -> Optional[Dict[str, Any]]:
        """Extract data from a single store element."""
        try:
            # Get the full text content of the store element
            full_text = await element.inner_text()
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            if not lines:
                return None
            
            # Parse the store information from the text
            # Expected format from exploration:
            # Line 0: Store name (e.g., "Prisma Tikkurila")
            # Line 1: Address (e.g., "Unikkotie 13, 01300 Vantaa")
            # Line 2: Hours (e.g., "Avoinna tänään: 06:00—00:00")
            # Line 3: "Tilaa verkosta" (optional)
            
            name = lines[0] if len(lines) > 0 else ""
            address = lines[1] if len(lines) > 1 else ""
            hours = lines[2] if len(lines) > 2 else ""
            
            # Extract city and postal code from address
            city = ""
            postal_code = ""
            if address:
                # Address format: "Street, PostalCode City"
                parts = address.split(',')
                if len(parts) >= 2:
                    location_part = parts[-1].strip()
                    location_words = location_part.split()
                    if len(location_words) >= 2 and location_words[0].isdigit():
                        postal_code = location_words[0]
                        city = ' '.join(location_words[1:])
            
            # Clean hours text
            if hours.startswith("Avoinna tänään:"):
                hours = hours.replace("Avoinna tänään:", "").strip()
            
            # Get href for additional info
            href = await element.get_attribute('href')
            
            if not name.strip():
                return None
                
            store_data = {
                'name': name.strip(),
                'address': address.strip(),
                'city': city,
                'postal_code': postal_code,
                'phone': '',  # Not available on listing page
                'hours': hours,
                'services': ['Tilaa verkosta'] if 'Tilaa verkosta' in full_text else [],
                'latitude': None,
                'longitude': None,
                'store_type': store_type,
                'store_url': href if href else '',
                'scraped_at': datetime.now().isoformat(),
                'source': 'browser'
            }
            
            return store_data
            
        except Exception as e:
            logger.error(f"Error extracting store data: {e}")
            return None

    async def scrape_stores(self) -> List[Dict[str, Any]]:
        """Main method to scrape store data."""
        logger.info("Starting S-kaupat scraping...")
        
        # Try API approach first if not forced to use browser
        if not self.use_browser and self.session:
            api_data = await self._try_api_approach()
            if api_data:
                logger.info(f"Successfully scraped {len(api_data)} stores via API")
                return api_data
                
        # Fallback to browser scraping
        if self.browser:
            browser_data = await self._scrape_with_browser()
            logger.info(f"Successfully scraped {len(browser_data)} stores via browser")
            return browser_data
            
        logger.error("No scraping method available")
        return []

    async def scrape_product(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single product from its URL."""
        if not self.browser:
            logger.error("Browser not initialized for product scraping")
            return None
            
        page = await self.browser.new_page()
        await page.set_extra_http_headers(DEFAULT_HEADERS)
        
        try:
            # Ensure we have a full URL
            if product_url.startswith('/'):
                full_url = f"{BASE_URL}{product_url}"
            else:
                full_url = product_url
                
            logger.info(f"Scraping product: {full_url}")
            
            # Navigate to product page
            await page.goto(full_url, wait_until='networkidle')
            await self._rate_limit()
            
            # Extract product data
            product_data = await self._extract_product_data(page, full_url)
            return product_data
            
        except Exception as e:
            logger.error(f"Error scraping product {product_url}: {e}")
            return None
        finally:
            await page.close()

    async def _extract_product_data(self, page, product_url: str) -> Optional[Dict[str, Any]]:
        """Extract product data from a product page."""
        try:
            # Extract product name
            name_element = await page.query_selector(PRODUCT_NAME_SELECTOR)
            name = await name_element.text_content() if name_element else ""
            
            if not name.strip():
                logger.warning(f"No product name found for {product_url}")
                return None
            
            # Extract price (get the first clean price)
            price = ""
            price_elements = await page.query_selector_all(PRODUCT_PRICE_SELECTOR)
            for element in price_elements:
                text = await element.text_content()
                # Look for clean price format like '0,17 €'
                if ('€' in text and ',' in text and len(text) < 15 and 
                    'Noin' not in text and 'Vertailu' not in text and 'kg' not in text):
                    price = text.strip()
                    break
            
            # Extract description (look for product-specific description)
            description = ""
            desc_elements = await page.query_selector_all(PRODUCT_DESCRIPTION_SELECTOR)
            for desc in desc_elements:
                text = await desc.text_content()
                # Look for meaningful product descriptions
                if (text and len(text) > 20 and len(text) < 500 and 
                    ('Class' in text or 'banaani' in text.lower() or 
                     any(keyword in text.lower() for keyword in ['tuote', 'product', 'ingredients', 'ainesosat']))):
                    description = text.strip()
                    break
            
            # If no specific description found, try to get the first reasonable paragraph
            if not description:
                for desc in desc_elements:
                    text = await desc.text_content()
                    if text and 30 < len(text) < 300 and '©' not in text:
                        description = text.strip()
                        break
            
            product_data = {
                'name': name.strip(),
                'price': price,
                'description': description,
                'url': product_url,
                'scraped_at': datetime.now().isoformat(),
                'source': 'browser'
            }
            
            logger.info(f"Successfully scraped product: {name}")
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None

    async def scrape_products(self, product_urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple products from their URLs."""
        logger.info(f"Starting to scrape {len(product_urls)} products...")
        
        if not self.browser:
            logger.error("Browser not initialized for product scraping")
            return []
        
        products = []
        
        for url in product_urls:
            try:
                async with self.semaphore:  # Rate limiting
                    product_data = await self.scrape_product(url)
                    if product_data:
                        products.append(product_data)
                    await self._rate_limit()
            except Exception as e:
                logger.error(f"Error processing product URL {url}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(products)} products")
        return products


async def run_scrape(use_browser: bool = False) -> List[Dict[str, Any]]:
    """Public function to run the store scraper.
    
    Args:
        use_browser: If True, force browser usage. If False, try API first.
        
    Returns:
        List of store data dictionaries.
    """
    async with SKaupatScraper(use_browser=use_browser) as scraper:
        return await scraper.scrape_stores()


async def run_product_scrape(product_urls: List[str]) -> List[Dict[str, Any]]:
    """Public function to run the product scraper.
    
    Args:
        product_urls: List of product URLs to scrape.
        
    Returns:
        List of product data dictionaries.
    """
    async with SKaupatScraper(use_browser=True) as scraper:
        return await scraper.scrape_products(product_urls)


async def scrape_single_product(product_url: str) -> Optional[Dict[str, Any]]:
    """Public function to scrape a single product.
    
    Args:
        product_url: Product URL to scrape.
        
    Returns:
        Product data dictionary or None if failed.
    """
    async with SKaupatScraper(use_browser=True) as scraper:
        return await scraper.scrape_product(product_url)


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    use_browser = "--browser" in sys.argv
    product_mode = "--product" in sys.argv
    
    async def main():
        if product_mode:
            # Test product scraping with sample URLs
            test_urls = [
                "https://www.s-kaupat.fi/tuote/chiquita-banaani/2000503600002",
                "https://www.s-kaupat.fi/tuote/kotimaista-kurkku/2000604700007",
                "https://www.s-kaupat.fi/tuote/porkkanapussi-500g/6414795733328",
            ]
            products = await run_product_scrape(test_urls)
            print(f"Scraped {len(products)} products")
            for product in products:
                print(f"- {product['name']}: {product['price']} - {product['description'][:50]}...")
        else:
            # Default store scraping
            stores = await run_scrape(use_browser=use_browser)
            print(f"Scraped {len(stores)} stores")
            for store in stores[:3]:  # Print first 3 for testing
                print(f"- {store['name']}: {store['address']}")
    
    asyncio.run(main())
