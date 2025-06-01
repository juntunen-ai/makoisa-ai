#!/usr/bin/env python3
"""
Analyze scraped products data and show statistics
"""

import json
import sys
from collections import Counter
from pathlib import Path

def analyze_products(file_path: str):
    """Analysoi raavitut tuotteet ja näyttää tilastoja."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Virhe tiedoston lukemisessa: {e}")
        return
    
    print(f"=== TUOTEANALYYSI: {file_path} ===\n")
    
    # Perustilastot
    total = len(products)
    successful = len([p for p in products if p.get('name')])
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"📊 PERUSTILASTOT:")
    print(f"   Tuotteita yhteensä: {total}")
    print(f"   Onnistuneet: {successful}")
    print(f"   Epäonnistuneet: {failed}")
    print(f"   Onnistumisprosentti: {success_rate:.1f}%\n")
    
    if successful == 0:
        print("❌ Ei onnistuneita tuotteita analysoitavaksi")
        return
    
    # Hintatilastot
    prices = []
    for p in products:
        if p.get('price') and '€' in str(p['price']):
            try:
                price_str = str(p['price']).replace('€', '').replace(',', '.').strip()
                price = float(price_str)
                prices.append(price)
            except:
                continue
    
    if prices:
        prices.sort()
        avg_price = sum(prices) / len(prices)
        median_price = prices[len(prices)//2]
        min_price = min(prices)
        max_price = max(prices)
        
        print(f"💰 HINTATILASTOT ({len(prices)} tuotetta):")
        print(f"   Keskihinta: {avg_price:.2f}€")
        print(f"   Mediaanihinta: {median_price:.2f}€")
        print(f"   Halvin: {min_price:.2f}€")
        print(f"   Kallein: {max_price:.2f}€\n")
    
    # Tuotetyyppianalyysi (nimen perusteella)
    product_keywords = Counter()
    for p in products:
        name = p.get('name', '').lower()
        if name:
            words = name.split()
            for word in words:
                if len(word) > 3:  # Vain yli 3 merkin sanat
                    product_keywords[word] += 1
    
    print(f"🏷️ YLEISIMMÄT SANAT TUOTENIMISSÄ:")
    for word, count in product_keywords.most_common(15):
        percentage = (count / successful * 100)
        print(f"   {word}: {count} ({percentage:.1f}%)")
    
    print(f"\n📝 ESIMERKKEJÄ TUOTTEISTA:")
    # Näytä erilaisia esimerkkejä
    examples = [p for p in products if p.get('name')][:10]
    for i, product in enumerate(examples, 1):
        name = product.get('name', 'N/A')[:50]
        price = product.get('price', 'N/A')
        print(f"   {i:2d}. {name} - {price}")

def main():
    if len(sys.argv) != 2:
        print("Käyttö: python analyze_products.py <tiedosto.json>")
        print("\nEtsi automaattisesti uusin tiedosto:")
        
        # Etsi uusimmat tiedostot
        import glob
        final_files = glob.glob("all_products_*.json")
        intermediate_files = glob.glob("intermediate_products_*.json")
        
        if final_files:
            latest = max(final_files, key=lambda f: Path(f).stat().st_mtime)
            print(f"  Uusin lopullinen: {latest}")
            analyze_products(latest)
        elif intermediate_files:
            latest = max(intermediate_files, key=lambda f: Path(f).stat().st_mtime)
            print(f"  Uusin välitulos: {latest}")
            analyze_products(latest)
        else:
            print("  Ei tulostiedostoja löytynyt")
        
        return
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"❌ Tiedostoa {file_path} ei löydy")
        return
    
    analyze_products(file_path)

if __name__ == "__main__":
    main()
