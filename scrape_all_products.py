#!/usr/bin/env python3
"""
Bulk product scraper for S-kaupat.fi
Raapii kaikki tuotteet löydetyistä URL:eista.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from scraper.main import run_product_scrape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkProductScraper:
    def __init__(self, urls_file: str = 'all_product_urls.json'):
        self.urls_file = urls_file
        self.output_file = f'all_products_scraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.batch_size = 50  # Prosessoi 50 tuotetta kerrallaan
        
    async def load_urls(self) -> List[str]:
        """Lataa tuote-URL:t tiedostosta."""
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                urls = json.load(f)
            logger.info(f"Ladattiin {len(urls)} URL:ää tiedostosta {self.urls_file}")
            return urls
        except FileNotFoundError:
            logger.error(f"Tiedostoa {self.urls_file} ei löytynyt!")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Virhe JSON:n lukemisessa: {e}")
            return []
    
    async def scrape_in_batches(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Raaputaa tuotteet erissä."""
        all_products = []
        total_batches = (len(urls) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"Aloitetaan raaputtaminen {total_batches} erässä ({self.batch_size} tuotetta/erä)")
        
        for i in range(0, len(urls), self.batch_size):
            batch_num = (i // self.batch_size) + 1
            batch_urls = urls[i:i + self.batch_size]
            
            logger.info(f"Käsitellään erä {batch_num}/{total_batches} ({len(batch_urls)} tuotetta)...")
            
            try:
                # Raaputaa tämä erä
                batch_products = await run_product_scrape(batch_urls)
                
                if batch_products:
                    all_products.extend(batch_products)
                    logger.info(f"Erä {batch_num} valmis: {len(batch_products)} tuotetta raavittiin")
                else:
                    logger.warning(f"Erä {batch_num}: Ei tuotteita raavittiin")
                
                # Tallenna välitulos
                if batch_num % 5 == 0:  # Tallenna joka 5. erän jälkeen
                    await self.save_intermediate_results(all_products, batch_num)
                
                # Odota hetki ennen seuraavaa erää
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Virhe erässä {batch_num}: {e}")
                continue
        
        return all_products
    
    async def save_intermediate_results(self, products: List[Dict[str, Any]], batch_num: int):
        """Tallenna välitulokset."""
        intermediate_file = f"intermediate_products_batch_{batch_num}.json"
        try:
            with open(intermediate_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logger.info(f"Välitulos tallennettu: {intermediate_file} ({len(products)} tuotetta)")
        except Exception as e:
            logger.error(f"Virhe välituloksen tallennuksessa: {e}")
    
    async def scrape_all_products(self):
        """Pääfunktio kaikkien tuotteiden raaputtamiseksi."""
        start_time = time.time()
        
        # Lataa URL:t
        urls = await self.load_urls()
        if not urls:
            logger.error("Ei URL:eitä raaputtavaksi!")
            return
        
        logger.info(f"Aloitetaan {len(urls)} tuotteen raaputtaminen...")
        
        # Raaputaa tuotteet
        all_products = await self.scrape_in_batches(urls)
        
        # Tallenna lopulliset tulokset
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, indent=2, ensure_ascii=False)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"VALMIS! Raavittiin {len(all_products)} tuotetta {duration/60:.1f} minuutissa")
            logger.info(f"Tulokset tallennettu: {self.output_file}")
            
            # Tilastot
            successful = len([p for p in all_products if p.get('name')])
            failed = len(all_products) - successful
            
            logger.info(f"Onnistuneet: {successful}")
            logger.info(f"Epäonnistuneet: {failed}")
            logger.info(f"Onnistumisprosentti: {(successful/len(all_products)*100):.1f}%")
            
        except Exception as e:
            logger.error(f"Virhe lopullisten tulosten tallennuksessa: {e}")

async def main():
    """Pääfunktio."""
    # Tarkista onko URL-tiedosto olemassa
    urls_file = 'all_product_urls.json'
    if not Path(urls_file).exists():
        logger.error(f"Tiedosto {urls_file} ei löydy!")
        logger.info("Aja ensin 'python discover_all_products.py' löytääksesi tuote-URL:t")
        return
    
    scraper = BulkProductScraper(urls_file)
    await scraper.scrape_all_products()

if __name__ == "__main__":
    asyncio.run(main())
