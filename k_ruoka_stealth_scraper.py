#!/usr/bin/env python3
"""
Advanced K-ruoka.fi scraper with comprehensive anti-bot bypass techniques.
"""

import asyncio
import json
import logging
import random
import time
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
import user_agents
import requests
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KRuokaStealhScraper:
    """Advanced K-ruoka scraper with anti-bot protection bypass."""
    
    def __init__(self):
        self.base_url = "https://www.k-ruoka.fi"
        self.scraped_products = []
        self.product_urls = []
        
        # Stealth settings
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864}
        ]
    
    async def create_stealth_browser(self):
        """Create a browser with stealth configuration."""
        p = await async_playwright().start()
        
        # Use launch_persistent_context instead for user data dir
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/k-ruoka-chrome-data',
            headless=False,  # Start non-headless for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-ipc-flooding-protection',
                '--enable-features=NetworkService,NetworkServiceLogging',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                '--disable-background-networking',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-sync',
                '--metrics-recording-only',
                '--no-report-upload'
            ]
        )
        
        # Random user agent and viewport
        user_agent = random.choice(self.user_agents)
        viewport = random.choice(self.viewports)
        
        # Set viewport and user agent on context
        await context.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': user_agent
        })
        
        return p, None, context
    
    async def setup_stealth_page(self, page: Page):
        """Configure page with stealth scripts."""
        
        # Remove automation indicators
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Add chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fi-FI', 'fi', 'en'],
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock battery API
            Object.defineProperty(navigator, 'getBattery', {
                get: () => () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                })
            });
            
            // Add realistic screen properties
            Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
        """)
        
        # Random mouse movements and realistic behavior
        await page.add_init_script("""
            // Add random mouse movements
            let lastActivity = Date.now();
            
            function randomMouseMove() {
                const x = Math.random() * window.innerWidth;
                const y = Math.random() * window.innerHeight;
                
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
                lastActivity = Date.now();
            }
            
            // Simulate random mouse movements
            setInterval(randomMouseMove, Math.random() * 5000 + 3000);
            
            // Simulate scroll behavior
            function randomScroll() {
                const scrollY = Math.random() * 100;
                window.scrollBy(0, scrollY);
                lastActivity = Date.now();
            }
            
            setInterval(randomScroll, Math.random() * 10000 + 5000);
        """)
    
    async def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add human-like random delays."""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def handle_cloudflare_challenge(self, page: Page) -> bool:
        """Attempt to handle Cloudflare challenge."""
        logger.info("Checking for Cloudflare challenge...")
        
        # Wait for potential challenge
        await asyncio.sleep(5)
        
        # Check for Cloudflare indicators
        cloudflare_selectors = [
            '#cf-wrapper',
            '.cf-browser-verification',
            '[data-ray]',
            'title:has-text("Just a moment")',
            'h1:has-text("Just a moment")',
            '.cf-error-title'
        ]
        
        for selector in cloudflare_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Cloudflare challenge detected with selector: {selector}")
                    
                    # Wait for challenge to complete (up to 30 seconds)
                    for _ in range(30):
                        await asyncio.sleep(1)
                        current_url = page.url
                        if 'challenge' not in current_url and 'cf-' not in current_url:
                            logger.info("Cloudflare challenge appears to be resolved")
                            return True
                    
                    logger.warning("Cloudflare challenge not resolved within timeout")
                    return False
            except:
                continue
        
        return True
    
    async def navigate_with_retry(self, page: Page, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                
                # Random delay before navigation
                await self.human_like_delay(1, 3)
                
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                if response and response.status == 200:
                    # Handle potential Cloudflare challenge
                    if await self.handle_cloudflare_challenge(page):
                        return True
                else:
                    logger.warning(f"Navigation returned status: {response.status if response else 'None'}")
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await self.human_like_delay(5, 10)  # Longer delay on retry
                
        return False
    
    async def accept_cookies(self, page: Page):
        """Accept cookies if prompt appears."""
        cookie_selectors = [
            'button:has-text("Hyväksy")',
            'button:has-text("Accept")',
            'button:has-text("Hyväksy kaikki")',
            'button[id*="accept"]',
            'button[class*="accept"]',
            '[data-testid*="accept"]',
            '.cookie-accept',
            '#cookie-accept'
        ]
        
        for selector in cookie_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await self.human_like_delay(0.5, 1.5)
                    await button.click()
                    logger.info(f"Accepted cookies with selector: {selector}")
                    await self.human_like_delay(1, 2)
                    return
            except:
                continue
    
    async def discover_product_urls(self, page: Page) -> List[str]:
        """Discover product URLs from the site."""
        product_urls = []
        
        try:
            # Navigate to main shop page
            if not await self.navigate_with_retry(page, f"{self.base_url}/kauppa"):
                return product_urls
            
            await self.accept_cookies(page)
            await self.human_like_delay(2, 4)
            
            # Try to find category links first
            category_selectors = [
                'a[href*="/kategoria/"]',
                'a[href*="/category/"]',
                'a[href*="/osasto/"]',
                '[data-testid*="category"] a',
                '.category-link',
                '.nav-category a'
            ]
            
            categories = []
            for selector in category_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in categories:
                                categories.append(full_url)
                except:
                    continue
            
            logger.info(f"Found {len(categories)} category URLs")
            
            # Explore categories to find products
            for category_url in categories[:10]:  # Limit to first 10 categories
                try:
                    if not await self.navigate_with_retry(page, category_url):
                        continue
                    
                    await self.human_like_delay(2, 4)
                    
                    # Look for product links
                    product_selectors = [
                        'a[href*="/tuote/"]',
                        'a[href*="/product/"]',
                        '[data-testid*="product"] a',
                        '.product-card a',
                        '.product-item a',
                        '[class*="product"] a'
                    ]
                    
                    for selector in product_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            for element in elements:
                                href = await element.get_attribute('href')
                                if href:
                                    full_url = urljoin(self.base_url, href)
                                    if full_url not in product_urls:
                                        product_urls.append(full_url)
                        except:
                            continue
                    
                    logger.info(f"Found {len(product_urls)} total product URLs so far")
                    
                    # Try pagination
                    next_selectors = [
                        'a:has-text("Seuraava")',
                        'a:has-text("Next")',
                        'button:has-text("Lisää")',
                        '[data-testid*="next"]',
                        '.pagination-next'
                    ]
                    
                    for next_selector in next_selectors:
                        try:
                            next_button = await page.query_selector(next_selector)
                            if next_button and await next_button.is_visible():
                                await next_button.click()
                                await self.human_like_delay(3, 5)
                                
                                # Get more products from next page
                                for selector in product_selectors:
                                    try:
                                        elements = await page.query_selector_all(selector)
                                        for element in elements:
                                            href = await element.get_attribute('href')
                                            if href:
                                                full_url = urljoin(self.base_url, href)
                                                if full_url not in product_urls:
                                                    product_urls.append(full_url)
                                    except:
                                        continue
                                break
                        except:
                            continue
                
                except Exception as e:
                    logger.warning(f"Error exploring category {category_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error discovering product URLs: {e}")
        
        logger.info(f"Total discovered product URLs: {len(product_urls)}")
        return product_urls
    
    async def scrape_product(self, page: Page, product_url: str) -> Optional[Dict]:
        """Scrape a single product from K-ruoka."""
        try:
            if not await self.navigate_with_retry(page, product_url):
                return None
            
            await self.human_like_delay(1, 3)
            
            product_data = {
                'url': product_url,
                'scraped_at': time.time(),
                'source': 'k-ruoka'
            }
            
            # Try to extract product name
            name_selectors = [
                'h1[data-testid*="product-name"]',
                'h1[data-testid*="title"]',
                '.product-title h1',
                '.product-name',
                'h1',
                '[data-testid*="name"]'
            ]
            
            for selector in name_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        name = await element.text_content()
                        if name and name.strip():
                            product_data['name'] = name.strip()
                            break
                except:
                    continue
            
            # Try to extract price
            price_selectors = [
                '[data-testid*="price"]',
                '.price-current',
                '.product-price',
                '.price',
                '[class*="price"]',
                'span:has-text("€")'
            ]
            
            for selector in price_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        price_text = await element.text_content()
                        if price_text and '€' in price_text:
                            product_data['price'] = price_text.strip()
                            break
                except:
                    continue
            
            # Try to extract description
            description_selectors = [
                '[data-testid*="description"]',
                '.product-description',
                '.description',
                'p',
                '[data-testid*="info"]'
            ]
            
            for selector in description_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        desc = await element.text_content()
                        if desc and desc.strip() and len(desc.strip()) > 10:
                            product_data['description'] = desc.strip()
                            break
                except:
                    continue
            
            if 'name' in product_data:
                logger.info(f"Successfully scraped: {product_data['name']}")
                return product_data
            else:
                logger.warning(f"Could not extract product name from {product_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping product {product_url}: {e}")
            return None
    
    async def run_discovery(self):
        """Run product URL discovery."""
        p, browser, context = await self.create_stealth_browser()
        
        try:
            page = await context.new_page()
            await self.setup_stealth_page(page)
            
            self.product_urls = await self.discover_product_urls(page)
            
            # Save discovered URLs
            with open('k_ruoka_product_urls.json', 'w', encoding='utf-8') as f:
                json.dump(self.product_urls, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.product_urls)} product URLs to k_ruoka_product_urls.json")
            
        finally:
            if context:
                await context.close()
            if p:
                await p.stop()
    
    async def run_scraping(self, max_products: int = 100):
        """Run product scraping."""
        # Load URLs if not already discovered
        if not self.product_urls:
            try:
                with open('k_ruoka_product_urls.json', 'r', encoding='utf-8') as f:
                    self.product_urls = json.load(f)
            except FileNotFoundError:
                logger.error("No product URLs found. Run discovery first.")
                return
        
        p, browser, context = await self.create_stealth_browser()
        
        try:
            page = await context.new_page()
            await self.setup_stealth_page(page)
            
            urls_to_scrape = self.product_urls[:max_products]
            logger.info(f"Starting to scrape {len(urls_to_scrape)} products")
            
            for i, url in enumerate(urls_to_scrape):
                logger.info(f"Scraping product {i+1}/{len(urls_to_scrape)}: {url}")
                
                product_data = await self.scrape_product(page, url)
                if product_data:
                    self.scraped_products.append(product_data)
                
                # Save progress every 10 products
                if (i + 1) % 10 == 0:
                    filename = f'k_ruoka_products_batch_{i+1}.json'
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.scraped_products, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved progress: {len(self.scraped_products)} products to {filename}")
                
                # Random delay between products
                await self.human_like_delay(2, 5)
            
            # Final save
            with open('k_ruoka_all_products.json', 'w', encoding='utf-8') as f:
                json.dump(self.scraped_products, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Scraping complete! Total products: {len(self.scraped_products)}")
            
        finally:
            if context:
                await context.close()
            if p:
                await p.stop()

async def main():
    """Main function to run the K-ruoka scraper."""
    scraper = KRuokaStealhScraper()
    
    # First discover product URLs
    logger.info("Starting product URL discovery...")
    await scraper.run_discovery()
    
    # Then scrape products
    logger.info("Starting product scraping...")
    await scraper.run_scraping(max_products=50)  # Start with 50 products

if __name__ == "__main__":
    asyncio.run(main())
