#!/usr/bin/env python3
"""
Monitor bulk scraping progress
"""

import json
import time
import glob
from pathlib import Path
from datetime import datetime

def monitor_progress():
    """Seuraa raaputtamisen edistymistä."""
    
    print("=== S-kaupat Bulk Scraping Monitor ===\n")
    
    while True:
        try:
            # Etsi kaikki tulostiedostot
            intermediate_files = glob.glob("intermediate_products_batch_*.json")
            final_files = glob.glob("all_products_*.json")
            
            print(f"📅 {datetime.now().strftime('%H:%M:%S')}")
            
            if intermediate_files:
                # Etsi viimeisin välitulos
                latest_intermediate = max(intermediate_files, key=lambda f: Path(f).stat().st_mtime)
                
                try:
                    with open(latest_intermediate, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                    
                    successful = len([p for p in products if p.get('name')])
                    failed = len(products) - successful
                    success_rate = (successful / len(products) * 100) if products else 0
                    
                    print(f"📊 Viimeisin välitulos ({latest_intermediate}):")
                    print(f"   Tuotteita käsitelty: {len(products)}")
                    print(f"   Onnistuneet: {successful}")
                    print(f"   Epäonnistuneet: {failed}")
                    print(f"   Onnistumisprosentti: {success_rate:.1f}%")
                    
                except Exception as e:
                    print(f"❌ Virhe välituloksen lukemisessa: {e}")
            
            if final_files:
                latest_final = max(final_files, key=lambda f: Path(f).stat().st_mtime)
                print(f"✅ Löytyi lopullinen tulos: {latest_final}")
                
                try:
                    with open(latest_final, 'r', encoding='utf-8') as f:
                        final_products = json.load(f)
                    
                    successful = len([p for p in final_products if p.get('name')])
                    failed = len(final_products) - successful
                    success_rate = (successful / len(final_products) * 100) if final_products else 0
                    
                    print(f"🎉 LOPULLINEN TULOS:")
                    print(f"   Kaikki tuotteet: {len(final_products)}")
                    print(f"   Onnistuneet: {successful}")
                    print(f"   Epäonnistuneet: {failed}")
                    print(f"   Onnistumisprosentti: {success_rate:.1f}%")
                    break
                    
                except Exception as e:
                    print(f"❌ Virhe lopullisen tuloksen lukemisessa: {e}")
            
            if not intermediate_files and not final_files:
                print("⏳ Ei vielä tuloksia...")
            
            print("-" * 50)
            time.sleep(30)  # Päivitä 30 sekunnin välein
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring pysäytetty")
            break
        except Exception as e:
            print(f"❌ Virhe seurannassa: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_progress()
