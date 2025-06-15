# crawler_pilote_complet.py
# -*- coding: utf-8 -*-
# VERSION FINALE AVEC LES SÉLECTEURS DE LA PAGE DE DÉTAIL CORRIGÉS

import time
import csv
import os
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import undetected_chromedriver as uc

def get_driver_urls(overview_url="https://www.formula1.com/en/drivers.html"):
    """
    Utilise undetected-chromedriver, le bon sélecteur et le bon filtre pour extraire les URLs.
    """
    print("Initialisation du navigateur non détectable...")
    driver = None
    urls = []
    
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = uc.Chrome(options=options)
        print(f"Navigation vers : {overview_url}")
        driver.get(overview_url)
        print("Attente de 15 secondes pour le chargement complet...")
        time.sleep(15)
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        potential_links = soup.select('a[href*="/en/drivers/"]')
        if not potential_links:
            print("!!! Aucun lien de pilote trouvé.")
            return []

        unique_urls = set()
        for link in potential_links:
            href = link.get('href', '')
            if href and href.strip() not in ['/en/drivers.html', '/en/drivers']:
                full_url = urljoin(overview_url, href)
                unique_urls.add(full_url)
        
        urls = sorted(list(unique_urls))
        if not urls:
             print("!!! Aucun lien de pilote spécifique n'a pu être isolé.")
             return []

        print(f"-> {len(urls)} URLs de pilotes uniques trouvées.")
    except Exception as e:
        print(f"!!! Une erreur est survenue lors de la récupération des URLs : {type(e).__name__} - {e}")
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
    return urls

def scrape_driver_page(driver_url, driver_instance):
    """
    Scrapes a single driver page, now including the main image URL.
    """
    print(f"--- Traitement de : {driver_url}")
    try:
        driver_instance.get(driver_url)
        time.sleep(4)
        html_content = driver_instance.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        driver_data = {'url': driver_url}

        def get_safe_text(element): return element.get_text(strip=True) if element else 'N/A'
        def get_safe_src(element): return element.get('src', '') if element else ''
        
        # --- Existing code for name and number (no changes here) ---
        name_element = soup.select_one("h1.f1-heading__body")
        driver_data['full_name'] = get_safe_text(name_element)

        number_container = soup.select_one(".f1-driver-position p.f1-heading")
        if number_container:
             driver_data['driver_number'] = number_container.get_text(strip=True, separator=' ').split(' ')[0]
        else:
             driver_data['driver_number'] = 'N/A'
             
        # --- START OF ADDITION ---
        # Select the main driver image and get its 'src' attribute
        image_element = soup.select_one("img.f1-c-image.aspect-square")
        driver_data['main_image_url'] = get_safe_src(image_element)
        # --- END OF ADDITION ---

        # --- Existing code for stats (no changes here) ---
        stats_mapping = {
            'Team': 'team', 'Country': 'country', 'Podiums': 'podiums', 'Points': 'points', 
            'Grands Prix entered': 'grands_prix_entered', 'World Championships': 'world_championships', 
            'Highest race finish': 'highest_race_finish', 'Highest grid position': 'highest_grid_position', 
            'Date of birth': 'date_of_birth', 'Place of birth': 'place_of_birth'
        }
        
        stats_list = soup.select_one("dl.f1-grid")
        if stats_list:
            all_labels = stats_list.find_all('dt')
            for label_dt in all_labels:
                label_text = label_dt.get_text(strip=True)
                if label_text in stats_mapping:
                    value_dd = label_dt.find_next_sibling('dd')
                    if value_dd:
                        driver_data[stats_mapping[label_text]] = value_dd.get_text(strip=True)
        
        if driver_data.get('full_name', 'N/A') != 'N/A':
            print(f"-> Données extraites pour {driver_data['full_name']}")
            return driver_data
        else:
            print(f"-> Nom du pilote non trouvé sur la page de détail, données ignorées.")
            return None
    except Exception as e:
        print(f"!!! Erreur lors du scraping de la page {driver_url}: {e}")
        traceback.print_exc()
        return None

def save_to_csv(data, filename):
    if not data: 
        print("Aucune donnée à sauvegarder.")
        return
    print(f"\nSauvegarde de {len(data)} pilotes dans {filename}...")
    
    # Add 'main_image_url' to the list of headers
    headers = [
        'full_name', 'driver_number', 'team', 'country', 'podiums', 'points',
        'grands_prix_entered', 'world_championships', 'highest_race_finish',
        'highest_grid_position', 'date_of_birth', 'place_of_birth', 
        'main_image_url', 'url'
    ]
    
    try:
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        print(f"-> Données sauvegardées avec succès.")
    except Exception as e: print(f"!!! ERREUR lors de la sauvegarde CSV : {e}")


if __name__ == "__main__":
    print("="*40)
    print(" F1 Driver Scraper - Version Finale et Complète")
    print("="*40)
    
    start_time = time.time()
    driver_urls = get_driver_urls()
    
    if driver_urls:
        all_drivers_data = []
        print("\nInitialisation du navigateur pour le scraping des pages individuelles...")
        scraper_options = uc.ChromeOptions()
        scraper_options.add_argument('--headless')
        driver_scraper = uc.Chrome(options=scraper_options)
        
        for url in driver_urls:
            data = scrape_driver_page(url, driver_scraper)
            if data:
                all_drivers_data.append(data)
            time.sleep(2)
            
        driver_scraper.quit()
        output_path = os.path.join("f1_driver_data", "f1_drivers_all.csv")
        save_to_csv(all_drivers_data, output_path)

    end_time = time.time()
    print("\n" + "="*40)
    print(f"Scraping terminé ! Temps total : {end_time - start_time:.2f} secondes.")
    print("="*40)