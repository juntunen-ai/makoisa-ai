#!/usr/bin/env python3
"""
Comprehensive product URL discovery script for S-kaupat.fi
Löytää kaikki tuotteet käyttämällä erilaisia strategioita.
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

class SKaupatProductDiscovery:
    def __init__(self):
        self.discovered_urls: Set[str] = set()
        self.base_url = "https://www.s-kaupat.fi"
        
    async def search_by_term(self, page, search_term: str) -> Set[str]:
        """Hae tuotteita hakutermillä."""
        try:
            await page.goto(self.base_url)
            await page.wait_for_timeout(2000)
            
            # Etsi hakukenttä
            search_input = await page.query_selector('input[type="search"], input[placeholder*="Hae"]')
            if not search_input:
                logger.warning("Hakukenttää ei löytynyt")
                return set()
            
            # Syötä hakutermi
            await search_input.fill(search_term)
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(3000)
            
            # Vieritä alas ladatakseen kaikki tulokset
            for _ in range(5):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)
            
            # Kerää tuotelinkit
            product_links = await page.query_selector_all('a[href*="/tuote/"]')
            urls = set()
            
            for link in product_links:
                href = await link.get_attribute('href')
                if href and '/tuote/' in href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    urls.add(href)
            
            logger.info(f"Haku '{search_term}': {len(urls)} tuotetta")
            return urls
            
        except Exception as e:
            logger.error(f"Virhe haussa '{search_term}': {e}")
            return set()
    
    async def discover_all_products(self):
        """Löydä kaikki tuotteet käyttämällä erilaisia strategioita."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info("Aloitetaan tuotteiden etsintä...")
            
            # Strategia 1: Aakkoset (a-z)
            logger.info("Strategia 1: Hakeminen aakkosilla")
            for letter in string.ascii_lowercase:
                urls = await self.search_by_term(page, letter)
                self.discovered_urls.update(urls)
                await asyncio.sleep(1)  # Viive
            
            # Strategia 2: Numerot (0-9)
            logger.info("Strategia 2: Hakeminen numeroilla")
            for digit in string.digits:
                urls = await self.search_by_term(page, digit)
                self.discovered_urls.update(urls)
                await asyncio.sleep(1)
            
            # Strategia 3: Yleiset hakutermit
            logger.info("Strategia 3: Yleiset hakutermit")
            common_terms = [
                'maito', 'leipä', 'liha', 'kala', 'vihannekset', 'hedelmät',
                'juoma', 'mehu', 'kahvi', 'tee', 'jäätelö', 'makeiset',
                'pasta', 'riisi', 'peruna', 'tomaatti', 'kurkku', 'salaatti',
                'juusto', 'kinkku', 'makke', 'jogurtti', 'kerma', 'voi',
                'oil', 'öljy', 'sieni', 'sipuli', 'porkkana', 'omena'
            ]
            
            for term in common_terms:
                urls = await self.search_by_term(page, term)
                self.discovered_urls.update(urls)
                await asyncio.sleep(1)
            
            # Strategia 4: Kaksoiskirjaimet
            logger.info("Strategia 4: Kaksoiskirjaimet")
            for letter in 'abcdefghijklmnopqrstuvwxyz':
                double_letter = letter + letter
                urls = await self.search_by_term(page, double_letter)
                self.discovered_urls.update(urls)
                await asyncio.sleep(1)
            
            await browser.close()
            
            logger.info(f"Löydettiin yhteensä {len(self.discovered_urls)} ainutlaatuista tuotetta")
            return list(self.discovered_urls)

async def main():
    """Pääfunktio tuotteiden etsimiseksi."""
    discovery = SKaupatProductDiscovery()
    
    start_time = time.time()
    all_urls = await discovery.discover_all_products()
    end_time = time.time()
    
    # Tallenna tulokset
    output_file = 'all_product_urls.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_urls, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Valmis! Löydettiin {len(all_urls)} tuotetta {end_time - start_time:.1f} sekunnissa")
    logger.info(f"URL:t tallennettu tiedostoon: {output_file}")
    
    # Näytä muutama esimerkkiä
    logger.info("Esimerkkejä löydetyistä tuotteista:")
    for i, url in enumerate(all_urls[:10]):
        logger.info(f"  {i+1}. {url}")

if __name__ == "__main__":
    asyncio.run(main())
