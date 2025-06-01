#!/usr/bin/env python3
"""
Simple K-ruoka exploration to find correct selectors.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def explore_k_ruoka():
    """Simple exploration of K-ruoka site structure."""
    
    async with async_playwright() as p:
        # Launch browser in non-headless mode to see what's happening
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to K-ruoka main page
            logger.info("Navigating to K-ruoka.fi...")
            await page.goto("https://www.k-ruoka.fi", wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Get page title and URL
            title = await page.title()
            url = page.url
            logger.info(f"Page title: {title}")
            logger.info(f"Current URL: {url}")
            
            # Accept cookies
            try:
                cookie_button = await page.query_selector('button:has-text("Hyväksy")')
                if cookie_button:
                    await cookie_button.click()
                    logger.info("Clicked cookie accept button")
                    await asyncio.sleep(2)
            except:
                logger.info("No cookie button found or already accepted")
            
            # Try to navigate to shop/kauppa section
            logger.info("Looking for shop/kauppa navigation...")
            
            # Try different approaches to find shop section
            shop_selectors = [
                'a[href*="kauppa"]',
                'a:has-text("Kauppa")',
                'a:has-text("Ostokset")',
                'nav a[href*="tuote"]',
                '[data-testid*="shop"]'
            ]
            
            found_shop = False
            for selector in shop_selectors:
                try:
                    shop_link = await page.query_selector(selector)
                    if shop_link:
                        href = await shop_link.get_attribute('href')
                        text = await shop_link.inner_text()
                        logger.info(f"Found shop link: {text} -> {href}")
                        
                        if href and 'kauppa' in href.lower():
                            await shop_link.click()
                            logger.info("Clicked shop link")
                            await asyncio.sleep(5)
                            found_shop = True
                            break
                except Exception as e:
                    logger.info(f"Error with selector {selector}: {e}")
                    continue
            
            if not found_shop:
                # Try direct navigation to shop
                logger.info("Trying direct navigation to /kauppa")
                await page.goto("https://www.k-ruoka.fi/kauppa", wait_until="networkidle")
                await asyncio.sleep(5)
            
            # Check current URL and title
            current_url = page.url
            current_title = await page.title()
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Current title: {current_title}")
            
            # Look for product categories
            logger.info("Looking for product categories...")
            
            category_selectors = [
                'a[href*="kategoria"]',
                'a[href*="category"]',
                'a[href*="osasto"]',
                '[data-testid*="category"]',
                '.category',
                'nav a',
                'a[href*="tuote"]'
            ]
            
            categories_found = []
            for selector in category_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"Selector '{selector}' found {len(elements)} elements")
                    
                    for element in elements[:5]:  # Check first 5 elements
                        try:
                            href = await element.get_attribute('href')
                            text = await element.inner_text()
                            if href and text:
                                categories_found.append((text.strip(), href))
                                logger.info(f"  - {text.strip()} -> {href}")
                        except:
                            continue
                except Exception as e:
                    logger.info(f"Error with category selector {selector}: {e}")
            
            logger.info(f"Total categories found: {len(categories_found)}")
            
            # Look for any product links on current page
            logger.info("Looking for product links...")
            
            product_selectors = [
                'a[href*="tuote"]',
                'a[href*="product"]',
                '[data-testid*="product"]',
                '.product',
                'a[href*="/p/"]'
            ]
            
            products_found = []
            for selector in product_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"Product selector '{selector}' found {len(elements)} elements")
                    
                    for element in elements[:3]:  # Check first 3 elements
                        try:
                            href = await element.get_attribute('href')
                            text = await element.inner_text()
                            if href:
                                products_found.append((text.strip() if text else "No text", href))
                                logger.info(f"  - {text.strip() if text else 'No text'} -> {href}")
                        except:
                            continue
                except Exception as e:
                    logger.info(f"Error with product selector {selector}: {e}")
            
            logger.info(f"Total products found: {len(products_found)}")
            
            # Keep browser open for manual inspection
            logger.info("Browser will stay open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_k_ruoka())
