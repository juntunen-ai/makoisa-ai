#!/usr/bin/env python3
"""
Explore K-ruoka.fi website structure to understand how to scrape products.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def explore_k_ruoka():
    """Explore K-ruoka.fi website structure."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to main page
            logger.info("Navigating to K-ruoka.fi...")
            await page.goto("https://www.k-ruoka.fi/kauppa")
            await page.wait_for_timeout(3000)
            
            # Check if there's a cookie consent
            await page.wait_for_timeout(2000)
            cookie_selectors = [
                'button:has-text("Hyväksy")',
                'button:has-text("Accept")',
                'button[id*="accept"]',
                'button[class*="accept"]',
                '[data-testid*="accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = await page.query_selector(selector)
                    if cookie_button and await cookie_button.is_visible():
                        await cookie_button.click()
                        await page.wait_for_timeout(1000)
                        logger.info(f"Clicked cookie consent with selector: {selector}")
                        break
                except:
                    continue
            
            # Look for search functionality
            logger.info("Looking for search functionality...")
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="Hae"]',
                'input[placeholder*="Search"]',
                '[data-testid*="search"]',
                '.search-input',
                '#search'
            ]
            
            search_input = None
            for selector in search_selectors:
                search_input = await page.query_selector(selector)
                if search_input:
                    logger.info(f"Found search input with selector: {selector}")
                    break
            
            if search_input:
                # Try a test search
                await search_input.fill("maito")
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(3000)
                
                # Look for product elements
                logger.info("Looking for product elements...")
                product_selectors = [
                    'a[href*="/tuote/"]',
                    'a[href*="/product/"]',
                    '[data-testid*="product"]',
                    '.product-card',
                    '.product-item',
                    '[class*="product"]'
                ]
                
                for selector in product_selectors:
                    products = await page.query_selector_all(selector)
                    if products:
                        logger.info(f"Found {len(products)} products with selector: {selector}")
                        
                        # Get a sample URL
                        if products:
                            sample_href = await products[0].get_attribute('href')
                            logger.info(f"Sample product URL: {sample_href}")
                        break
                
                # Look for product details structure
                logger.info("Looking for product details structure...")
                detail_selectors = [
                    '[data-testid*="name"], .product-name, .product-title, h1, h2, h3',
                    '[data-testid*="price"], .price, .product-price, [class*="price"]',
                    '[data-testid*="description"], .description, .product-description, p'
                ]
                
                for selector in detail_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} detail elements with selector: {selector}")
                        if elements:
                            sample_text = await elements[0].text_content()
                            logger.info(f"Sample text: {sample_text[:100]}...")
            
            # Look for category navigation
            logger.info("Looking for category navigation...")
            category_selectors = [
                'a[href*="/kategoria/"]',
                'a[href*="/category/"]',
                '[data-testid*="category"]',
                '.category',
                '.nav-item'
            ]
            
            for selector in category_selectors:
                categories = await page.query_selector_all(selector)
                if categories:
                    logger.info(f"Found {len(categories)} categories with selector: {selector}")
                    break
            
            logger.info("Exploration complete. Taking a screenshot...")
            await page.screenshot(path='k_ruoka_exploration.png')
            
        except Exception as e:
            logger.error(f"Error during exploration: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_k_ruoka())
