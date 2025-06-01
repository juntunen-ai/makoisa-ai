#!/usr/bin/env python3
"""
Advanced K-ruoka.fi scraper with enhanced anti-bot bypass techniques.
Uses undetected-chromedriver with more sophisticated evasion methods.
"""

import asyncio
import json
import logging
import random
import time
import requests
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from urllib.parse import urljoin, urlparse
import user_agents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KRuokaAdvancedScraper:
    """Advanced K-ruoka scraper with enhanced anti-bot bypass."""
    
    def __init__(self):
        self.base_url = "https://www.k-ruoka.fi"
        self.scraped_products = []
        self.product_urls = []
        self.driver = None
        
        # Enhanced stealth settings
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
    def create_stealth_driver(self):
        """Create a Chrome driver with advanced stealth configuration."""
        try:
            # Create Chrome options
            options = Options()
            
            # Basic stealth options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Faster loading
            options.add_argument('--disable-javascript')  # Start without JS, enable later if needed
            options.add_argument('--user-agent=' + random.choice(self.user_agents))
            
            # Anti-detection options
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Create undetected Chrome driver
            driver = uc.Chrome(options=options, version_main=None)
            
            # Execute stealth scripts
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set a more realistic window size
            driver.set_window_size(1920, 1080)
            
            self.driver = driver
            logger.info("Successfully created stealth Chrome driver")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create stealth driver: {e}")
            return None
    
    def human_like_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add human-like delay between actions."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def accept_cookies(self, driver):
        """Accept cookies if prompt appears."""
        cookie_selectors = [
            '//button[contains(text(), "Hyväksy")]',
            '//button[contains(text(), "Accept")]',
            '//button[contains(text(), "Hyväksy kaikki")]',
            '//button[@id[contains(., "accept")]]',
            '//button[@class[contains(., "accept")]]'
        ]
        
        for selector in cookie_selectors:
            try:
                wait = WebDriverWait(driver, 3)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if button:
                    self.human_like_delay(0.5, 1.5)
                    button.click()
                    logger.info(f"Accepted cookies with selector: {selector}")
                    self.human_like_delay(1, 2)
                    return True
            except TimeoutException:
                continue
        return False
    
    def navigate_with_retry(self, driver, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                
                # Random delay before navigation
                self.human_like_delay(1, 3)
                
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check if we got blocked
                if "403" in driver.title or "Forbidden" in driver.page_source:
                    logger.warning(f"Got 403 error on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        self.human_like_delay(5, 10)
                        continue
                    return False
                
                logger.info(f"Successfully navigated to {url}")
                return True
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    self.human_like_delay(5, 10)
                
        return False
    
    def discover_product_urls(self, driver) -> List[str]:
        """Discover product URLs using a different approach."""
        product_urls = []
        
        try:
            # First, try to find the main navigation or category links
            logger.info("Looking for main navigation...")
            
            # Try different approaches to find categories
            category_approaches = [
                # Approach 1: Look for direct category links
                {
                    'name': 'Direct category links',
                    'selectors': [
                        '//a[contains(@href, "kategoria")]',
                        '//a[contains(@href, "category")]',
                        '//a[contains(@href, "osasto")]'
                    ]
                },
                # Approach 2: Look for navigation menus
                {
                    'name': 'Navigation menus',
                    'selectors': [
                        '//nav//a',
                        '//ul[@class[contains(., "nav")]]//a',
                        '//div[@class[contains(., "menu")]]//a'
                    ]
                },
                # Approach 3: Look for any links that might lead to products
                {
                    'name': 'Product-related links',
                    'selectors': [
                        '//a[contains(@href, "tuote")]',
                        '//a[contains(@href, "product")]',
                        '//a[contains(text(), "Tuotteet")]',
                        '//a[contains(text(), "Products")]'
                    ]
                }
            ]
            
            categories_found = []
            
            for approach in category_approaches:
                logger.info(f"Trying approach: {approach['name']}")
                
                for selector in approach['selectors']:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        logger.info(f"  Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements[:10]:  # Limit to first 10
                            try:
                                href = element.get_attribute('href')
                                text = element.text.strip()
                                
                                if href and href not in categories_found:
                                    categories_found.append(href)
                                    logger.info(f"    - {text}: {href}")
                                    
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        logger.info(f"  Error with selector {selector}: {e}")
                        continue
                
                if categories_found:
                    logger.info(f"Found {len(categories_found)} potential category URLs")
                    break
            
            # If we found categories, explore them
            if categories_found:
                logger.info(f"Exploring {len(categories_found)} category URLs...")
                
                for i, category_url in enumerate(categories_found[:5]):  # Limit to first 5
                    try:
                        logger.info(f"Exploring category {i+1}: {category_url}")
                        
                        if not self.navigate_with_retry(driver, category_url):
                            continue
                        
                        self.human_like_delay(2, 4)
                        
                        # Look for product links on this category page
                        product_selectors = [
                            '//a[contains(@href, "tuote")]',
                            '//a[contains(@href, "product")]',
                            '//div[@class[contains(., "product")]]//a',
                            '//article//a',
                            '//li[@class[contains(., "product")]]//a'
                        ]
                        
                        for selector in product_selectors:
                            try:
                                elements = driver.find_elements(By.XPATH, selector)
                                for element in elements:
                                    href = element.get_attribute('href')
                                    if href and href not in product_urls:
                                        product_urls.append(href)
                            except:
                                continue
                        
                        logger.info(f"Found {len(product_urls)} total product URLs so far")
                        
                        if len(product_urls) >= 100:  # Stop when we have enough
                            break
                            
                    except Exception as e:
                        logger.error(f"Error exploring category {category_url}: {e}")
                        continue
            
            else:
                logger.warning("No category URLs found. Trying direct product search...")
                
                # Try to find products directly on the main page
                product_selectors = [
                    '//a[contains(@href, "tuote")]',
                    '//a[contains(@href, "product")]',
                    '//div[@class[contains(., "product")]]//a'
                ]
                
                for selector in product_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and href not in product_urls:
                                product_urls.append(href)
                    except:
                        continue
                
        except Exception as e:
            logger.error(f"Error in discover_product_urls: {e}")
        
        logger.info(f"Total discovered product URLs: {len(product_urls)}")
        return product_urls
    
    def run_discovery(self):
        """Run product URL discovery."""
        driver = self.create_stealth_driver()
        if not driver:
            logger.error("Failed to create driver")
            return
        
        try:
            # Navigate to main K-ruoka page first
            if not self.navigate_with_retry(driver, self.base_url):
                logger.error("Failed to navigate to main page")
                return
            
            self.accept_cookies(driver)
            self.human_like_delay(2, 4)
            
            # Try to navigate to shop section
            shop_urls = [
                f"{self.base_url}/kauppa",
                f"{self.base_url}/tuotteet",
                f"{self.base_url}/products"
            ]
            
            shop_loaded = False
            for shop_url in shop_urls:
                if self.navigate_with_retry(driver, shop_url):
                    shop_loaded = True
                    break
            
            if not shop_loaded:
                logger.warning("Could not load shop section, continuing with main page")
            
            # Discover product URLs
            self.product_urls = self.discover_product_urls(driver)
            
            # Save discovered URLs
            with open('k_ruoka_product_urls.json', 'w', encoding='utf-8') as f:
                json.dump(self.product_urls, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.product_urls)} product URLs to k_ruoka_product_urls.json")
            
        finally:
            if driver:
                driver.quit()

def main():
    """Main function to run the K-ruoka scraper."""
    scraper = KRuokaAdvancedScraper()
    
    # Run discovery
    logger.info("Starting advanced K-ruoka product URL discovery...")
    scraper.run_discovery()

if __name__ == "__main__":
    main()
