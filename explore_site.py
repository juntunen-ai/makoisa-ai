"""Simple test to explore S-kaupat.fi structure."""

import asyncio
from playwright.async_api import async_playwright


async def explore_site():
    """Explore the S-kaupat.fi website structure."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Non-headless to see what happens
        page = await browser.new_page()
        
        try:
            # Navigate to main page
            await page.goto("https://www.s-kaupat.fi", wait_until='networkidle')
            
            # Get page title and take screenshot
            title = await page.title()
            print(f"Page title: {title}")
            
            # Look for any elements that might contain store information
            selectors_to_try = [
                'a[href*="kauppa"]',
                'a[href*="store"]',
                'a[href*="myymälä"]',
                '[data-testid*="store"]',
                '[data-testid*="location"]',
                '.store', '.location', '.branch',
                'nav a', 'footer a'
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\nFound {len(elements)} elements with selector '{selector}':")
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = await elem.inner_text()
                            href = await elem.get_attribute('href') if await elem.get_attribute('href') else ''
                            print(f"  {i+1}: '{text}' -> {href}")
                except Exception as e:
                    print(f"Error with selector '{selector}': {e}")
            
            # Check for location-based features
            print("\n--- Checking for location features ---")
            try:
                # Check if there's a postal code input or location selector
                postal_inputs = await page.query_selector_all('input[placeholder*="postinumero"], input[placeholder*="postal"], input[type="search"]')
                print(f"Found {len(postal_inputs)} potential postal code inputs")
                
                # Check for any mention of delivery areas or stores
                page_content = await page.content()
                keywords = ['myymälä', 'kauppa', 'toimitus', 'delivery', 'store', 'branch']
                for keyword in keywords:
                    if keyword.lower() in page_content.lower():
                        print(f"Found keyword '{keyword}' in page content")
                        
            except Exception as e:
                print(f"Error checking location features: {e}")
            
            # Wait a bit to see the page
            await asyncio.sleep(3)
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_site())
