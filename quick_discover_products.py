#!/usr/bin/env python3
"""
Quick product discovery script - finds product URLs faster with targeted searches
"""

import asyncio
import json
import logging
from typing import Set
from playwright.async_api import async_playwright
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_discovery():
    """Nopea tuotteiden etsintä kohdennetuilla hauilla."""
    
    # Tehokkaat hakutermit jotka todennäköisesti kattavat useimmat tuotteet
    targeted_searches = [
        # Peruselintarvikkeet
        'maito', 'leipä', 'liha', 'kala', 'kana', 'sika', 'nauta',
        'vihannekset', 'hedelmät', 'peruna', 'tomaatti', 'kurkku',
        'sipuli', 'porkkana', 'omena', 'banaani', 'sitruuna',
        
        # Meijerituotteet
        'juusto', 'jogurtti', 'kerma', 'voi', 'margariini',
        
        # Kuivattavarat
        'pasta', 'riisi', 'makaroni', 'spaghetti', 'ohra', 'kaura',
        
        # Juomat
        'mehu', 'limu', 'kahvi', 'tee', 'olut', 'viini', 'vesi',
        
        # Makeiset ja jälkiruuat
        'suklaa', 'makeisset', 'jäätelö', 'kakku', 'keks',
        
        # Säilykkeet
        'säilyke', 'tomaattimurska', 'herneet', 'pavut',
        
        # Pakasteet
        'pakaste', 'jäätelö', 'pakastevihannekset',
        
        # Kotitaloustuotteet  
        'pesuaine', 'shampoo', 'saippua', 'deodorantti',
        
        # Merkit (tunnetut brändit)
        'valio', 'atria', 'hk', 'saarioinen', 'paulig', 'fazer',
        'kaleva', 'arla', 'danone', 'coca cola', 'pepsi',
        
        # Yleiset hakutermit
        'luomu', 'gluteeniton', 'laktoositon', 'kevyt', 'täysjyvä'
    ]
    
    discovered_urls = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        logger.info(f"Aloitetaan nopea etsintä {len(targeted_searches)} hakutermillä...")
        
        for i, term in enumerate(targeted_searches, 1):
            try:
                await page.goto('https://www.s-kaupat.fi/')
                await page.wait_for_timeout(1000)
                
                # Hae
                search_input = await page.query_selector('input[type="search"], input[placeholder*="Hae"]')
                if search_input:
                    await search_input.fill(term)
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(2000)
                    
                    # Vieritä alas
                    for _ in range(3):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(500)
                    
                    # Kerää URL:t
                    product_links = await page.query_selector_all('a[href*="/tuote/"]')
                    batch_urls = set()
                    
                    for link in product_links:
                        href = await link.get_attribute('href')
                        if href and '/tuote/' in href:
                            if href.startswith('/'):
                                href = 'https://www.s-kaupat.fi' + href
                            batch_urls.add(href)
                    
                    discovered_urls.update(batch_urls)
                    logger.info(f"[{i}/{len(targeted_searches)}] '{term}': {len(batch_urls)} uutta, yhteensä {len(discovered_urls)}")
                    
                    await asyncio.sleep(0.5)  # Lyhyt viive
                    
            except Exception as e:
                logger.error(f"Virhe haussa '{term}': {e}")
                continue
        
        await browser.close()
    
    return list(discovered_urls)

async def main():
    start_time = time.time()
    
    urls = await quick_discovery()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Tallenna
    output_file = 'quick_product_urls.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Nopea etsintä valmis! {len(urls)} URL:ää {duration:.1f} sekunnissa")
    logger.info(f"Tallennettu: {output_file}")
    
    # Esimerkkejä
    for i, url in enumerate(urls[:5]):
        logger.info(f"  {i+1}. {url}")

if __name__ == "__main__":
    asyncio.run(main())
