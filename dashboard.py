#!/usr/bin/env python3
"""
S-kaupat Bulk Scraping Dashboard - Complete status overview
"""

import json
import time
import glob
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_process_status(pattern):
    """Tarkista onko prosessi käynnissä."""
    try:
        result = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True)
        return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except:
        return 0

def format_time_ago(file_path):
    """Laske kuinka kauan sitten tiedosto on muutettu."""
    try:
        mtime = Path(file_path).stat().st_mtime
        diff = time.time() - mtime
        if diff < 60:
            return f"{int(diff)}s sitten"
        elif diff < 3600:
            return f"{int(diff//60)}min sitten"
        else:
            return f"{int(diff//3600)}h {int((diff%3600)//60)}min sitten"
    except:
        return "tuntematon"

def dashboard():
    """Näytä kokonaisvaltainen tilannekatsaus."""
    
    print("=" * 60)
    print("🍎 S-KAUPAT BULK SCRAPING DASHBOARD")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Prosessien tila
    print("\n🔄 KÄYNNISSÄ OLEVAT PROSESSIT:")
    discovery_processes = get_process_status('discover_all_products')
    scraping_processes = get_process_status('scrape-all-products')
    monitor_processes = get_process_status('monitor_progress')
    
    if discovery_processes > 0:
        print(f"   🔍 URL-etsintä: {discovery_processes} prosessia")
    if scraping_processes > 0:
        print(f"   🤖 Tuote-raapinta: {scraping_processes} prosessia")
    if monitor_processes > 0:
        print(f"   📊 Seuranta: {monitor_processes} prosessia")
    
    if discovery_processes + scraping_processes + monitor_processes == 0:
        print("   ⏸️ Ei aktiivisia prosesseja")
    
    # 2. URL-tiedostot
    print("\n📂 URL-TIEDOSTOT:")
    url_files = ['all_product_urls.json', 'quick_product_urls.json']
    
    for file in url_files:
        if Path(file).exists():
            try:
                with open(file, 'r') as f:
                    urls = json.load(f)
                age = format_time_ago(file)
                print(f"   ✅ {file}: {len(urls)} URL:ää ({age})")
            except:
                print(f"   ❌ {file}: virhe lukemisessa")
        else:
            print(f"   ⭕ {file}: ei löydy")
    
    # 3. Raaputtamistulokset
    print("\n📊 RAAPUTTAMISTULOKSET:")
    
    # Välitulokset
    intermediate_files = glob.glob("intermediate_products_batch_*.json")
    if intermediate_files:
        latest_intermediate = max(intermediate_files, key=lambda f: Path(f).stat().st_mtime)
        try:
            with open(latest_intermediate, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            successful = len([p for p in products if p.get('name')])
            failed = len(products) - successful
            success_rate = (successful / len(products) * 100) if products else 0
            age = format_time_ago(latest_intermediate)
            
            print(f"   🔄 Viimeisin välitulos ({Path(latest_intermediate).name}):")
            print(f"      Tuotteita: {len(products)} | Onnistuneet: {successful} | Epäonnistuneet: {failed}")
            print(f"      Onnistumisprosentti: {success_rate:.1f}% | Päivitetty: {age}")
            
        except Exception as e:
            print(f"   ❌ Virhe välituloksen lukemisessa: {e}")
    
    # Lopulliset tulokset
    final_files = glob.glob("all_products_*.json")
    if final_files:
        latest_final = max(final_files, key=lambda f: Path(f).stat().st_mtime)
        try:
            with open(latest_final, 'r', encoding='utf-8') as f:
                final_products = json.load(f)
            
            successful = len([p for p in final_products if p.get('name')])
            failed = len(final_products) - successful
            success_rate = (successful / len(final_products) * 100) if final_products else 0
            age = format_time_ago(latest_final)
            
            print(f"   🎉 LOPULLINEN TULOS ({Path(latest_final).name}):")
            print(f"      Kaikki tuotteet: {len(final_products)} | Onnistuneet: {successful}")
            print(f"      Onnistumisprosentti: {success_rate:.1f}% | Luotu: {age}")
            
        except Exception as e:
            print(f"   ❌ Virhe lopullisen tuloksen lukemisessa: {e}")
    
    if not intermediate_files and not final_files:
        print("   ⏳ Ei vielä raaputtamistuloksia")
    
    # 4. Tilastoja
    if intermediate_files or final_files:
        print("\n📈 TILASTOJA:")
        
        # Etsi paras tulos
        best_file = None
        best_count = 0
        
        for file_pattern in [final_files, intermediate_files]:
            for file in file_pattern:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                    if len(products) > best_count:
                        best_count = len(products)
                        best_file = file
                except:
                    continue
        
        if best_file and best_count > 0:
            print(f"   📊 Suurin tuotemäärä: {best_count} ({Path(best_file).name})")
            
            # Arvio kokonaisajasta
            if 'intermediate' in best_file:
                batch_num = int(best_file.split('_')[-1].split('.')[0])
                estimated_total_batches = 166  # Tiedämme että 4126 tuotetta / 25 = 166 erää
                if batch_num > 0:
                    progress_pct = (batch_num / estimated_total_batches) * 100
                    print(f"   📊 Arvioitu edistyminen: {progress_pct:.1f}% ({batch_num}/{estimated_total_batches} erää)")
    
    # 5. Käyttövinkkejä
    print("\n💡 HYÖDYLLISIÄ KOMENTOJA:")
    print("   📊 Analysoi tuloksia: python analyze_products.py")
    print("   🔍 Tarkastele edistymistä: python monitor_progress.py")
    print("   ⏹️ Pysäytä prosessit: pkill -f 'discover_all_products|scrape-all-products'")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    dashboard()
