#!/usr/bin/env python3
"""Explore a specific store type page structure in headless mode."""

import asyncio
from playwright.async_api import async_playwright

async def explore_prisma_page_headless():
    """Explore the Prisma store page structure in headless mode."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            
            # Get all text content first to understand the page
            body_text = await page.inner_text('body')
            lines = [line.strip() for line in body_text.split('\n') if line.strip()]
            
            print(f"\n=== Page has {len(lines)} lines of content ===")
            print(f"First 30 lines:")
            for i, line in enumerate(lines[:30]):
                print(f"{i+1:2}: {line}")
            
            print(f"\nLast 10 lines:")
            for i, line in enumerate(lines[-10:], len(lines)-9):
                print(f"{i:2}: {line}")
            
            # Look for specific patterns that might indicate stores
            store_patterns = ['Prisma', 'kauppakeskus', 'osoite', 'katu', 'aukiolo', 'puhelin']
            print(f"\n=== Looking for store-related patterns ===")
            for pattern in store_patterns:
                matching_lines = [line for line in lines if pattern.lower() in line.lower()]
                if matching_lines:
                    print(f"\nLines containing '{pattern}' ({len(matching_lines)} matches):")
                    for line in matching_lines[:5]:  # Show first 5 matches
                        print(f"  - {line}")
                    if len(matching_lines) > 5:
                        print(f"  ... and {len(matching_lines) - 5} more")
            
            # Try common selectors
            selectors_to_try = [
                'div[data-testid*="store"]',
                'div[data-testid*="location"]', 
                '.store-card',
                '.location-item',
                'li',
                'article',
                '.card',
                'a[href*="prisma"]',
                'div:has-text("Prisma")',
            ]
            
            print(f"\n=== Testing selectors ===")
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\nSelector '{selector}' found {len(elements)} elements")
                        
                        # Show content of first element
                        if elements:
                            first_text = await elements[0].inner_text()
                            print(f"First element text: {first_text[:200]}...")
                            
                except Exception as e:
                    print(f"Error with selector '{selector}': {e}")
            
            # Check the page URL to see if it redirected
            current_url = page.url
            print(f"\nCurrent URL: {current_url}")
            
            # Take a screenshot for debugging
            await page.screenshot(path="prisma_page.png", full_page=True)
            print("Screenshot saved as prisma_page.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_prisma_page_headless())
