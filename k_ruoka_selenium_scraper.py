#!/usr/bin/env python3
"""
K-ruoka scraper using Selenium with undetected-chromedriver for anti-bot bypass.
"""

import json
import logging
import random
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from urllib.parse import urljoin
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KRuokaSeleniumScraper:
    """K-ruoka scraper using Selenium with anti-bot evasion."""
    
    def __init__(self):
        self.base_url = "https://www.k-ruoka.fi"
        self.driver = None
        self.scraped_products = []
        self.product_urls = []
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
    
    def create_driver(self):
        """Create undetected Chrome driver."""
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--enable-features=NetworkService,NetworkServiceLogging')
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Random window size
        widths = [1920, 1366, 1440, 1536]
        heights = [1080, 768, 900, 864]
        width = random.choice(widths)
        height = random.choice(heights)
        options.add_argument(f'--window-size={width},{height}')
        
        # Language and locale
        options.add_argument('--lang=fi-FI')
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'fi-FI,fi,en-US,en'
        })
        
        # Create driver
        try:
            self.driver = uc.Chrome(options=options, version_main=120)
            
            # Execute stealth scripts
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['fi-FI', 'fi', 'en'],
                });
            """)
            
            logger.info("Created undetected Chrome driver successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create driver: {e}")
            return False
    
    def human_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add human-like delay."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def random_mouse_movement(self):
        """Simulate random mouse movements."""
        try:
            actions = ActionChains(self.driver)
            
            # Get window size
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            # Random movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(0, width)
                y = random.randint(0, height)
                actions.move_by_offset(x, y)
                self.human_delay(0.1, 0.5)
            
            actions.perform()
        except:
            pass
    
    def navigate_with_retry(self, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                self.human_delay(1, 3)
                
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check for Cloudflare or bot detection
                if self.handle_anti_bot_measures():
                    return True
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    self.human_delay(5, 10)
        
        return False
    
    def handle_anti_bot_measures(self) -> bool:
        """Handle various anti-bot measures."""
        # Check current URL and page content
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        
        # Cloudflare detection
        if any(indicator in page_source for indicator in ['cloudflare', 'just a moment', 'checking your browser']):
            logger.info("Cloudflare challenge detected, waiting...")
            
            # Wait up to 30 seconds for challenge to resolve
            for _ in range(30):
                time.sleep(1)
                if 'cloudflare' not in self.driver.page_source.lower():
                    logger.info("Cloudflare challenge resolved")
                    return True
            
            logger.warning("Cloudflare challenge not resolved")
            return False
        
        # Bot detection page
        if any(indicator in page_source for indicator in ['blocked', 'access denied', 'bot detected']):
            logger.warning("Bot detection page detected")
            return False
        
        # CAPTCHA detection
        if any(indicator in page_source for indicator in ['captcha', 'recaptcha', 'hcaptcha']):
            logger.warning("CAPTCHA detected - manual intervention needed")
            input("Please solve the CAPTCHA manually and press Enter to continue...")
            return True
        
        return True
    
    def accept_cookies(self):
        """Accept cookies if prompt appears."""
        cookie_selectors = [
            "//button[contains(text(), 'Hyväksy')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Hyväksy kaikki')]",
            "//button[@id[contains(., 'accept')]]",
            "//button[@class[contains(., 'accept')]]",
        ]
        
        for selector in cookie_selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                self.human_delay(0.5, 1.5)
                element.click()
                logger.info(f"Accepted cookies with selector: {selector}")
                self.human_delay(1, 2)
                return
            except TimeoutException:
                continue
    
    def discover_product_urls(self) -> List[str]:
        """Discover product URLs from K-ruoka."""
        product_urls = []
        
        if not self.navigate_with_retry(f"{self.base_url}/kauppa"):
            return product_urls
        
        self.accept_cookies()
        self.human_delay(2, 4)
        self.random_mouse_movement()
        
        # Look for category links
        category_selectors = [
            "//a[contains(@href, '/kategoria/')]",
            "//a[contains(@href, '/category/')]",
            "//a[contains(@href, '/osasto/')]"
        ]
        
        categories = set()
        for selector in category_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    href = element.get_attribute('href')
                    if href:
                        categories.add(href)
            except:
                continue
        
        logger.info(f"Found {len(categories)} category URLs")
        
        # Explore categories
        for category_url in list(categories)[:10]:  # Limit to first 10
            try:
                if not self.navigate_with_retry(category_url):
                    continue
                
                self.human_delay(2, 4)
                self.random_mouse_movement()
                
                # Scroll to load more products
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                self.human_delay(2, 3)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.human_delay(2, 3)
                
                # Look for product links
                product_selectors = [
                    "//a[contains(@href, '/tuote/')]",
                    "//a[contains(@href, '/product/')]"
                ]
                
                for selector in product_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and href not in product_urls:
                                product_urls.append(href)
                    except:
                        continue
                
                logger.info(f"Found {len(product_urls)} total product URLs so far")
                
                # Try to click "Load more" or pagination
                load_more_selectors = [
                    "//button[contains(text(), 'Lisää')]",
                    "//button[contains(text(), 'Load more')]",
                    "//a[contains(text(), 'Seuraava')]",
                    "//button[@data-testid[contains(., 'load-more')]]"
                ]
                
                for selector in load_more_selectors:
                    try:
                        button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView();", button)
                        self.human_delay(1, 2)
                        button.click()
                        self.human_delay(3, 5)
                        
                        # Get additional products after loading more
                        for prod_selector in product_selectors:
                            try:
                                elements = self.driver.find_elements(By.XPATH, prod_selector)
                                for element in elements:
                                    href = element.get_attribute('href')
                                    if href and href not in product_urls:
                                        product_urls.append(href)
                            except:
                                continue
                        break
                    except TimeoutException:
                        continue
                
            except Exception as e:
                logger.warning(f"Error exploring category {category_url}: {e}")
                continue
        
        logger.info(f"Total discovered product URLs: {len(product_urls)}")
        return product_urls
    
    def scrape_product(self, product_url: str) -> Optional[Dict]:
        """Scrape a single product."""
        try:
            if not self.navigate_with_retry(product_url):
                return None
            
            self.human_delay(1, 3)
            self.random_mouse_movement()
            
            product_data = {
                'url': product_url,
                'scraped_at': time.time(),
                'source': 'k-ruoka'
            }
            
            # Extract product name
            name_selectors = [
                "//h1[@data-testid[contains(., 'product-name')]]",
                "//h1[@data-testid[contains(., 'title')]]",
                "//h1[contains(@class, 'product-title')]",
                "//h1",
                "//*[@data-testid[contains(., 'name')]]"
            ]
            
            for selector in name_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    name = element.text.strip()
                    if name:
                        product_data['name'] = name
                        break
                except NoSuchElementException:
                    continue
            
            # Extract price
            price_selectors = [
                "//*[@data-testid[contains(., 'price')]]",
                "//*[contains(@class, 'price-current')]",
                "//*[contains(@class, 'product-price')]",
                "//*[contains(@class, 'price')]",
                "//*[contains(text(), '€')]"
            ]
            
            for selector in price_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    price_text = element.text.strip()
                    if price_text and '€' in price_text:
                        product_data['price'] = price_text
                        break
                except NoSuchElementException:
                    continue
            
            # Extract description
            desc_selectors = [
                "//*[@data-testid[contains(., 'description')]]",
                "//*[contains(@class, 'product-description')]",
                "//*[contains(@class, 'description')]",
                "//p[string-length(text()) > 10]"
            ]
            
            for selector in desc_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    desc = element.text.strip()
                    if desc and len(desc) > 10:
                        product_data['description'] = desc
                        break
                except NoSuchElementException:
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
    
    def run_discovery(self):
        """Run product URL discovery."""
        if not self.create_driver():
            return
        
        try:
            self.product_urls = self.discover_product_urls()
            
            # Save discovered URLs
            with open('k_ruoka_selenium_urls.json', 'w', encoding='utf-8') as f:
                json.dump(self.product_urls, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.product_urls)} product URLs to k_ruoka_selenium_urls.json")
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def run_scraping(self, max_products: int = 50):
        """Run product scraping."""
        # Load URLs if not already discovered
        if not self.product_urls:
            try:
                with open('k_ruoka_selenium_urls.json', 'r', encoding='utf-8') as f:
                    self.product_urls = json.load(f)
            except FileNotFoundError:
                logger.error("No product URLs found. Run discovery first.")
                return
        
        if not self.create_driver():
            return
        
        try:
            urls_to_scrape = self.product_urls[:max_products]
            logger.info(f"Starting to scrape {len(urls_to_scrape)} products")
            
            for i, url in enumerate(urls_to_scrape):
                logger.info(f"Scraping product {i+1}/{len(urls_to_scrape)}: {url}")
                
                product_data = self.scrape_product(url)
                if product_data:
                    self.scraped_products.append(product_data)
                
                # Save progress every 10 products
                if (i + 1) % 10 == 0:
                    filename = f'k_ruoka_selenium_batch_{i+1}.json'
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.scraped_products, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved progress: {len(self.scraped_products)} products to {filename}")
                
                # Random delay between products
                self.human_delay(2, 5)
            
            # Final save
            with open('k_ruoka_selenium_all_products.json', 'w', encoding='utf-8') as f:
                json.dump(self.scraped_products, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Scraping complete! Total products: {len(self.scraped_products)}")
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function."""
    scraper = KRuokaSeleniumScraper()
    
    # First discover URLs
    logger.info("Starting product URL discovery with Selenium...")
    scraper.run_discovery()
    
    # Then scrape products
    logger.info("Starting product scraping with Selenium...")
    scraper.run_scraping(max_products=30)

if __name__ == "__main__":
    main()
