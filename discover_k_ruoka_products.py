#!/usr/bin/env python3
"""
Discover product URLs from K-ruoka.fi using search functionality.
"""

import asyncio
import json
import logging
from typing import Set, List
from playwright.async_api import async_playwright
import time
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KRuokaProductDiscovery:
    def __init__(self):
        self.discovered_urls: Set[str] = set()
        self.base_url = "https://www.k-ruoka.fi"
        
    async def search_by_term(self, page, search_term: str) -> Set[str]:
        """Search for products using a search term."""
        try:
            await page.goto(f"{self.base_url}/kauppa")
            await page.wait_for_timeout(3000)
            
            # Handle cookie consent if present
            cookie_selectors = [
                'button:has-text("Hyväksy")',
                'button:has-text("Accept")',
                'button[id*="accept"]',
                'button[class*="accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = await page.query_selector(selector)
                    if cookie_button and await cookie_button.is_visible():
                        await cookie_button.click()
                        await page.wait_for_timeout(1000)
                        break
                except:
                    continue
            
            # Find search input
            search_input = await page.query_selector('input[type="search"]')
            if not search_input:
                logger.warning("Search input not found")
                return set()
            
            # Perform search
            await search_input.fill(search_term)
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(3000)
            
            # Scroll to load more products
            for _ in range(5):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)
            
            # Look for product links with various selectors
            product_urls = set()
            product_selectors = [
                'a[href*="/tuote/"]',
                'a[href*="/product/"]',
                'a[href*="/kauppa/tuote/"]',
                '[data-testid*="product"] a',
                '.product-card a',
                '.product-item a'
            ]
            
            for selector in product_selectors:
                try:
                    product_links = await page.query_selector_all(selector)
                    for link in product_links:
                        href = await link.get_attribute('href')
                        if href and ('/tuote/' in href or '/product/' in href):
                            if href.startswith('/'):
                                href = self.base_url + href
                            product_urls.add(href)
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
            
            # Alternative: look for any links that might be products
            if not product_urls:
                all_links = await page.query_selector_all('a[href]')
                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and any(keyword in href.lower() for keyword in ['tuote', 'product', 'item']):
                        if href.startswith('/'):
                            href = self.base_url + href
                        product_urls.add(href)
            
            logger.info(f"Search '{search_term}': {len(product_urls)} products found")
            return product_urls
            
        except Exception as e:
            logger.error(f"Error searching for '{search_term}': {e}")
            return set()
    
    async def discover_products_by_categories(self, page) -> Set[str]:
        """Discover products by browsing categories."""
        try:
            await page.goto(f"{self.base_url}/kauppa")
            await page.wait_for_timeout(3000)
            
            # Look for category links
            category_selectors = [
                'a[href*="/kategoria/"]',
                'a[href*="/category/"]',
                'a[href*="/kauppa/"] + a',
                '.category a',
                '.nav-item a'
            ]
            
            category_urls = set()
            for selector in category_selectors:
                try:
                    category_links = await page.query_selector_all(selector)
                    for link in category_links:
                        href = await link.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                href = self.base_url + href
                            category_urls.add(href)
                except:
                    continue
            
            logger.info(f"Found {len(category_urls)} category URLs")
            
            # Visit each category and collect product URLs
            product_urls = set()
            for category_url in list(category_urls)[:10]:  # Limit to first 10 categories
                try:
                    await page.goto(category_url)
                    await page.wait_for_timeout(2000)
                    
                    # Scroll to load products
                    for _ in range(3):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(1000)
                    
                    # Collect product URLs from this category
                    product_selectors = [
                        'a[href*="/tuote/"]',
                        'a[href*="/product/"]',
                        '[data-testid*="product"] a'
                    ]
                    
                    for selector in product_selectors:
                        try:
                            product_links = await page.query_selector_all(selector)
                            for link in product_links:
                                href = await link.get_attribute('href')
                                if href and ('/tuote/' in href or '/product/' in href):
                                    if href.startswith('/'):
                                        href = self.base_url + href
                                    product_urls.add(href)
                        except:
                            continue
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error browsing category {category_url}: {e}")
                    continue
            
            logger.info(f"Found {len(product_urls)} products from categories")
            return product_urls
            
        except Exception as e:
            logger.error(f"Error discovering by categories: {e}")
            return set()
    
    async def discover_all_products(self):
        """Discover all products using multiple strategies."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info("Starting K-ruoka.fi product discovery...")
            
            # Strategy 1: Search by common terms
            logger.info("Strategy 1: Searching by common terms")
            common_terms = [
                'maito', 'leipä', 'liha', 'kala', 'vihannekset', 'hedelmät',
                'juoma', 'kahvi', 'tee', 'pasta', 'riisi', 'juusto',
                'jogurtti', 'peruna', 'tomaatti', 'omena', 'banaani'
            ]
            
            for term in common_terms:
                urls = await self.search_by_term(page, term)
                self.discovered_urls.update(urls)
                await asyncio.sleep(2)  # Rate limiting
            
            # Strategy 2: Browse categories
            logger.info("Strategy 2: Browsing categories")
            category_urls = await self.discover_products_by_categories(page)
            self.discovered_urls.update(category_urls)
            
            # Strategy 3: Search by letters
            logger.info("Strategy 3: Searching by letters")
            for letter in 'abcdefghijklm':  # Limit to prevent too many requests
                urls = await self.search_by_term(page, letter)
                self.discovered_urls.update(urls)
                await asyncio.sleep(2)
            
            await browser.close()
            
            logger.info(f"Discovery complete! Found {len(self.discovered_urls)} unique products")
            return list(self.discovered_urls)

async def main():
    """Main function to discover K-ruoka products."""
    discovery = KRuokaProductDiscovery()
    
    start_time = time.time()
    all_urls = await discovery.discover_all_products()
    end_time = time.time()
    
    # Save results
    output_file = 'k_ruoka_product_urls.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_urls, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Complete! Found {len(all_urls)} products in {end_time - start_time:.1f} seconds")
    logger.info(f"URLs saved to: {output_file}")
    
    # Show some examples
    if all_urls:
        logger.info("Sample product URLs:")
        for i, url in enumerate(all_urls[:10]):
            logger.info(f"  {i+1}. {url}")

if __name__ == "__main__":
    asyncio.run(main())
