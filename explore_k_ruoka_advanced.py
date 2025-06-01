#!/usr/bin/env python3
"""
Advanced K-ruoka.fi exploration with anti-bot handling
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def explore_k_ruoka_advanced():
    """Explore K-ruoka.fi with advanced anti-bot evasion."""
    
    async with async_playwright() as p:
        # Use more realistic browser settings
        browser = await p.chromium.launch(
            headless=False,  # Start with non-headless to see what's happening
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Create context with more realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fi-FI',
            timezone_id='Europe/Helsinki'
        )
        
        page = await context.new_page()
        
        # Hide automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fi-FI', 'fi', 'en-US', 'en'],
            });
        """)
        
        try:
            logger.info("Navigating to K-ruoka.fi...")
            
            # Try direct navigation first
            response = await page.goto('https://www.k-ruoka.fi/kauppa', 
                                     wait_until='networkidle', 
                                     timeout=30000)
            
            logger.info(f"Initial response status: {response.status if response else 'No response'}")
            
            # Wait a bit and take a screenshot
            await page.wait_for_timeout(5000)
            await page.screenshot(path='k_ruoka_initial.png', full_page=True)
            
            # Check for various anti-bot challenges
            page_content = await page.content()
            
            if "verify that you are human" in page_content.lower() or "cloudflare" in page_content.lower():
                logger.info("Anti-bot challenge detected. Waiting and trying to solve...")
                
                # Wait longer for potential automatic bypass
                await page.wait_for_timeout(10000)
                
                # Check for challenge forms or buttons
                challenge_selectors = [
                    'input[type="checkbox"]',
                    'button[type="submit"]',
                    '.cf-turnstile',
                    '#challenge-form',
                    '[data-testid="cf-turnstile"]'
                ]
                
                for selector in challenge_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"Found challenge element: {selector}")
                        try:
                            await element.click()
                            await page.wait_for_timeout(3000)
                        except Exception as e:
                            logger.info(f"Could not interact with {selector}: {e}")
                
                # Wait for potential redirect
                await page.wait_for_timeout(10000)
                await page.screenshot(path='k_ruoka_after_challenge.png', full_page=True)
            
            # Try to find search functionality
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            
            # Look for search input
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="hae"]', 
                'input[placeholder*="Hae"]',
                'input[placeholder*="etsi"]',
                'input[placeholder*="Etsi"]',
                '.search-input',
                '[data-testid="search-input"]',
                '#search',
                '.searchbox input'
            ]
            
            search_input = None
            for selector in search_selectors:
                search_input = await page.query_selector(selector)
                if search_input:
                    logger.info(f"Found search input: {selector}")
                    break
            
            if search_input:
                # Try a simple search
                await search_input.fill("maito")
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(5000)
                
                # Look for product links
                product_selectors = [
                    'a[href*="/tuotteet/"]',
                    'a[href*="/tuote/"]', 
                    'a[href*="/product/"]',
                    '.product-card a',
                    '.product-item a',
                    '[data-testid="product-link"]'
                ]
                
                products_found = 0
                for selector in product_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        products_found += len(elements)
                        logger.info(f"Found {len(elements)} products with selector: {selector}")
                        
                        # Get some example URLs
                        for i, element in enumerate(elements[:3]):
                            href = await element.get_attribute('href')
                            if href:
                                logger.info(f"  Example product URL {i+1}: {href}")
                
                await page.screenshot(path='k_ruoka_search_results.png', full_page=True)
                logger.info(f"Total products found: {products_found}")
            else:
                logger.warning("No search input found")
            
            # Try to find category/navigation links
            nav_selectors = [
                'nav a',
                '.navigation a',
                '.menu a',
                '.category a',
                '[data-testid="category-link"]'
            ]
            
            categories_found = 0
            for selector in nav_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    categories_found += len(elements)
                    logger.info(f"Found {len(elements)} navigation links with selector: {selector}")
            
            logger.info(f"Total navigation links found: {categories_found}")
            
        except Exception as e:
            logger.error(f"Error during exploration: {e}")
            await page.screenshot(path='k_ruoka_error.png', full_page=True)
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_k_ruoka_advanced())
