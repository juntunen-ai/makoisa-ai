"""Test the stores page structure."""

import asyncio
from playwright.async_api import async_playwright


async def test_stores_page():
    """Test what's on the stores page."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to stores page
            print("Navigating to stores page...")
            await page.goto("https://www.s-kaupat.fi/myymalat", wait_until='networkidle')
            
            title = await page.title()
            print(f"Page title: {title}")
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Look for store-related elements
            selectors_to_try = [
                '.store', '.shop', '.myymala', '.kauppa',
                '[data-testid*="store"]', '[data-testid*="shop"]',
                '.card', '.item', '.location',
                'h1', 'h2', 'h3', 'h4',
                'ul li', 'ol li',
                'a[href*="myymala"]', 'a[href*="kauppa"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\nFound {len(elements)} elements with selector '{selector}':")
                        for i, elem in enumerate(elements[:5]):  # Show first 5
                            text = (await elem.inner_text()).strip()[:100]  # First 100 chars
                            href = await elem.get_attribute('href') if await elem.get_attribute('href') else ''
                            if text:
                                print(f"  {i+1}: '{text}' -> {href}")
                except Exception as e:
                    print(f"Error with selector '{selector}': {e}")
            
            # Get page content snippet
            print("\n--- Page content sample ---")
            content = await page.content()
            print(content[:1000] + "..." if len(content) > 1000 else content)
            
            # Wait to see the page
            await asyncio.sleep(5)
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_stores_page())
