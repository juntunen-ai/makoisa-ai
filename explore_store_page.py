#!/usr/bin/env python3
"""Explore a specific store type page to understand the structure."""

import asyncio
from playwright.async_api import async_playwright

async def explore_prisma_page():
    """Explore the Prisma store page structure."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        page = await browser.new_page()
        
        try:
            # Navigate to Prisma stores page
            url = "https://www.s-kaupat.fi/myymalat/prisma"
            print(f"Navigating to: {url}")
            
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)  # Let page fully load
            
            # Get page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Try to find store-related elements
            selectors_to_try = [
                'div[data-testid*="store"]',
                'div[data-testid*="location"]',
                '.store-card',
                '.location-item',
                '.store-info',
                '.card',
                'article',
                '.store',
                '[class*="store"]',
                '[class*="location"]',
                'li',
                'div[role="listitem"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\n=== Found {len(elements)} elements with selector: {selector} ===")
                        
                        # Show first few elements
                        for i, element in enumerate(elements[:3]):
                            try:
                                text = await element.inner_text()
                                html = await element.inner_html()
                                print(f"\nElement {i+1}:")
                                print(f"Text: {text[:200]}...")
                                print(f"HTML: {html[:300]}...")
                            except:
                                pass
                        
                        if len(elements) > 3:
                            print(f"... and {len(elements) - 3} more elements")
                            
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            # Check if there's a "Load more" or pagination
            load_more_selectors = [
                'button[aria-label*="load"]',
                'button[aria-label*="more"]',
                '.load-more',
                '.pagination',
                'button:has-text("Näytä lisää")',
                'button:has-text("Lataa lisää")',
            ]
            
            print(f"\n=== Checking for load more buttons ===")
            for selector in load_more_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"Found {len(elements)} load more elements with: {selector}")
                except:
                    pass
            
            # Get all text content to see what's actually on the page
            body_text = await page.inner_text('body')
            lines = [line.strip() for line in body_text.split('\n') if line.strip()]
            
            print(f"\n=== First 20 lines of page content ===")
            for i, line in enumerate(lines[:20]):
                print(f"{i+1}: {line}")
            
            # Wait a bit to see the page
            await asyncio.sleep(10)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_prisma_page())
