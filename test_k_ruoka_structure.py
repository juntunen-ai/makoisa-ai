#!/usr/bin/env python3
"""
Quick test to explore K-ruoka.fi structure and find correct selectors.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_k_ruoka_structure():
    """Test K-ruoka site structure to find correct selectors."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to K-ruoka
            logger.info("Navigating to K-ruoka.fi...")
            await page.goto("https://www.k-ruoka.fi", wait_until="networkidle")
            await asyncio.sleep(5)
            
            # Get page title and URL to confirm we're in the right place
            title = await page.title()
            url = page.url
            logger.info(f"Page title: {title}")
            logger.info(f"Current URL: {url}")
            
            # Accept cookies if present
            cookie_selectors = [
                'button[id*="accept"]',
                'button[class*="accept"]',
                'button:has-text("Hyväksy")',
                'button:has-text("Accept")',
                '[data-testid*="accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        logger.info(f"Clicking cookie accept button: {selector}")
                        await button.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Look for main navigation or category links
            logger.info("Looking for navigation links...")
            
            # Try different selectors for main navigation
            nav_selectors = [
                'nav a',
                '.main-nav a',
                '.navigation a',
                '[data-testid*="nav"] a',
                'header a',
                '.menu a'
            ]
            
            all_links = []
            for selector in nav_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"Found {len(elements)} links with selector: {selector}")
                    
                    for element in elements:
                        href = await element.get_attribute('href')
                        text = await element.inner_text()
                        if href and text:
                            all_links.append({
                                'text': text.strip(),
                                'href': href,
                                'selector': selector
                            })
                except Exception as e:
                    logger.info(f"Error with selector {selector}: {e}")
            
            # Print unique links
            unique_links = {}
            for link in all_links:
                if link['href'] not in unique_links:
                    unique_links[link['href']] = link
            
            logger.info(f"\nFound {len(unique_links)} unique links:")
            for href, link in list(unique_links.items())[:20]:  # Show first 20
                logger.info(f"  {link['text'][:50]} -> {href}")
            
            # Look specifically for kauppa/shop page
            logger.info("\nLooking for shop/kauppa page...")
            shop_selectors = [
                'a[href*="kauppa"]',
                'a[href*="shop"]',
                'a:has-text("Kauppa")',
                'a:has-text("Shop")',
                'a:has-text("Verkkokauppa")'
            ]
            
            shop_links = []
            for selector in shop_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        text = await element.inner_text()
                        if href:
                            shop_links.append({'text': text, 'href': href})
                except:
                    continue
            
            logger.info(f"Found {len(shop_links)} shop links:")
            for link in shop_links:
                logger.info(f"  {link['text']} -> {link['href']}")
            
            # Take a screenshot for reference
            await page.screenshot(path='k_ruoka_homepage.png')
            logger.info("Screenshot saved as k_ruoka_homepage.png")
            
        except Exception as e:
            logger.error(f"Error during exploration: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_k_ruoka_structure())
