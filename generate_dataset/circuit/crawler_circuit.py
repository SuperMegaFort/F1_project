# crawler_circuits_v4.py
# -*- coding: utf-8 -*-
# SCRAPER POUR LES CIRCUITS F1 - SÉLECTEURS CORRIGÉS ET AJOUT DU DRAPEAU

import time
import csv
import os
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# Utilisation de la bibliothèque qui simule un vrai navigateur humain
import undetected_chromedriver as uc

# --- DONNÉES MANUELLES POUR LES IMAGES ---
# Dictionnaire des URLs d'images de tracé correctes
circuits_manual_image_data = {
    'bahrain': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Bahrain_Circuit.png',
    'jeddah': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Saudi_Arabia_Circuit.png',
    'albert_park': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Australia_Circuit.png',
    'baku': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Baku_Circuit.png',
    'miami': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Miami_Circuit.png',
    'imola': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Emilia_Romagna_Circuit.png',
    'monaco': 'https://media.formula1.com/image/upload/f_auto,c_limit,q_auto,w_1320/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Monaco_Circuit',
    'catalunya': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Spain_Circuit.png',
    'villeneuve': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Canada_Circuit.png',
    'red_bull_ring': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Austria_Circuit.png',
    'silverstone': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Great_Britain_Circuit.png',
    'hungaroring': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Hungary_Circuit.png',
    'spa': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Belgium_Circuit.png',
    'zandvoort': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Netherlands_Circuit.png',
    'monza': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Italy_Circuit.png',
    'marina_bay': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Singapore_Circuit.png',
    'suzuka': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Japan_Circuit.png',
    'losail': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Qatar_Circuit.png',
    'americas': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/USA_Circuit.png',
    'rodriguez': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Mexico_Circuit.png',
    'interlagos': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Brazil_Circuit.png',
    'vegas': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Las_Vegas_Circuit.png',
    'yas_marina': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Abu_Dhabi_Circuit.png',
    'ricard': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/France_Circuit.png',
    'shanghai': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/China_Circuit.png'
}

# Mapping pour faire le lien entre l'URL et l'ID du circuit dans notre dictionnaire manuel
URL_SLUG_TO_CIRCUIT_ID = {
    'bahrain': 'bahrain', 'saudi-arabia': 'jeddah', 'australia': 'albert_park',
    'japan': 'suzuka', 'china': 'shanghai', 'miami': 'miami', 'emiliaromagna': 'imola',
    'monaco': 'monaco', 'canada': 'villeneuve', 'spain': 'catalunya', 'austria': 'red_bull_ring',
    'great-britain': 'silverstone', 'hungary': 'hungaroring', 'belgium': 'spa',
    'netherlands': 'zandvoort', 'italy': 'monza', 'azerbaijan': 'baku',
    'singapore': 'marina_bay', 'united-states': 'americas', 'mexico': 'rodriguez',
    'brazil': 'interlagos', 'las-vegas': 'vegas', 'qatar': 'losail',
    'abudhabi': 'yas_marina', 'united-arab-emirates': 'yas_marina'
}


def get_all_circuit_urls(season_url="https://www.formula1.com/en/racing/2024.html"):
    """
    Scrape une page de saison pour trouver les URLs de toutes les pages de détail des circuits.
    """
    print("Étape 1: Récupération des URLs des courses de la saison...")
    driver = None
    race_urls = []
    
    options = uc.ChromeOptions()
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = uc.Chrome(options=options)
        print(f"Navigation vers la page de la saison : {season_url}")
        driver.get(season_url)
        time.sleep(10)
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        links = soup.select("a.group[href*='/racing/']")
        if not links:
            print("!!! Aucun lien de course trouvé sur la page de la saison.")
            return []

        for link in links:
            href = link.get('href', '')
            if not "testing" in href:
                 race_urls.append(urljoin(season_url, href))
        
        unique_race_urls = sorted(list(set(race_urls)))
        print(f"-> {len(unique_race_urls)} URLs de courses trouvées.")

        print("\nÉtape 2: Récupération des URLs de détail des circuits...")
        circuit_urls = set()
        for i, race_url in enumerate(unique_race_urls):
            print(f"  - Analyse de la course {i+1}/{len(unique_race_urls)}: {race_url}")
            driver.get(race_url)
            time.sleep(3)
            race_html = driver.page_source
            race_soup = BeautifulSoup(race_html, 'html.parser')
            
            circuit_link = race_soup.select_one("a[href$='/circuit']")
            if circuit_link:
                circuit_detail_url = urljoin(race_url, circuit_link['href'])
                circuit_urls.add(circuit_detail_url)
                print(f"    -> Lien du circuit trouvé : {circuit_detail_url}")
            else:
                print(f"    -> AVERTISSEMENT: Pas de lien de circuit trouvé sur {race_url}")

    except Exception as e:
        print(f"!!! Une erreur est survenue : {type(e).__name__} - {e}")
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            
    final_urls = sorted(list(circuit_urls))
    print(f"\n-> {len(final_urls)} URLs de circuits uniques à scraper.")
    return final_urls

def scrape_circuit_page(circuit_url, driver_instance):
    """
    Scrape les informations d'une seule page de détail de circuit.
    """
    print(f"--- Traitement de : {circuit_url}")
    try:
        driver_instance.get(circuit_url)
        time.sleep(4)
        html_content = driver_instance.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        circuit_data = {'url': circuit_url}

        def get_safe_text(element): return element.get_text(strip=True) if element else 'N/A'
        def get_safe_src(element): return element.get('src', '') if element else ''
        
        # Sélecteur corrigé pour le nom du circuit
        circuit_data['circuit_name'] = get_safe_text(soup.select_one("h2.f1-heading__body div"))
        
        # Ajout de l'URL du drapeau du pays
        flag_element = soup.select_one("img[alt$='-flag.png']")
        circuit_data['country_flag_url'] = get_safe_src(flag_element)
        
        # Utilisation des images manuelles pour le tracé
        try:
            url_path = urlparse(circuit_url).path
            slug = url_path.split('/')[-2]
            circuit_id = URL_SLUG_TO_CIRCUIT_ID.get(slug)
            if circuit_id:
                circuit_data['image_url'] = circuits_manual_image_data.get(circuit_id, '')
                print(f"    -> Image manuelle trouvée pour {slug} -> {circuit_id}")
            else:
                circuit_data['image_url'] = ''
                print(f"    -> AVERTISSEMENT: Slug '{slug}' non trouvé dans le mapping d'images.")
        except Exception:
            circuit_data['image_url'] = ''

        # Extraction des statistiques
        stats_mapping = {
            'First Grand Prix': 'first_gp', 'Number of Laps': 'laps',
            'Circuit Length': 'length_km', 'Race Distance': 'race_distance_km',
            'Lap Record': 'lap_record_time'
        }
        
        stat_containers = soup.select("div.f1-grid > div[class*='border-']")
        for container in stat_containers:
            label_element = container.select_one("span.f1-text")
            value_element = container.select_one("h2.f1-heading")

            if label_element and value_element:
                label = label_element.get_text(strip=True)
                value = value_element.find(string=True, recursive=False).strip()
                
                if label in stats_mapping:
                    circuit_data[stats_mapping[label]] = value
                
                if label == 'Lap Record':
                    driver_span = value_element.select_one("span.f1-text")
                    circuit_data['lap_record_driver'] = get_safe_text(driver_span).replace('(','').replace(')','') if driver_span else 'N/A'

        if circuit_data.get('circuit_name', 'N/A') not in ['N/A', '']:
            print(f"-> Données extraites pour {circuit_data['circuit_name']}")
            return circuit_data
        else:
            print(f"-> Nom du circuit non trouvé, données ignorées.")
            return None
            
    except Exception as e:
        print(f"!!! Erreur lors du scraping de la page {circuit_url}: {e}")
        traceback.print_exc()
        return None


def save_to_csv(data, filename):
    if not data: 
        print("Aucune donnée de circuit à sauvegarder.")
        return
        
    print(f"\nSauvegarde de {len(data)} circuits dans {filename}...")
    # Ajout de la nouvelle colonne pour le drapeau
    headers = [
        'circuit_name', 'length_km', 'laps', 'race_distance_km', 'first_gp', 
        'lap_record_time', 'lap_record_driver', 'image_url', 'country_flag_url', 'url'
    ]
    try:
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        print(f"-> Données sauvegardées avec succès.")
    except Exception as e: 
        print(f"!!! ERREUR lors de la sauvegarde CSV : {e}")


if __name__ == "__main__":
    YEAR_TO_SCRAPE = 2024
    
    print("="*40)
    print(f" F1 Circuit Scraper pour la saison {YEAR_TO_SCRAPE}")
    print("="*40)
    
    start_time = time.time()
    season_url = f"https://www.formula1.com/en/racing/{YEAR_TO_SCRAPE}.html"
    circuit_urls = get_all_circuit_urls(season_url)
    
    if circuit_urls:
        all_circuits_data = []
        print("\nInitialisation du navigateur pour le scraping des pages de détail...")
        scraper_options = uc.ChromeOptions()
        scraper_options.add_argument('--headless')
        driver_scraper = uc.Chrome(options=scraper_options)
        
        for url in circuit_urls:
            data = scrape_circuit_page(url, driver_scraper)
            if data:
                all_circuits_data.append(data)
            time.sleep(2)
            
        driver_scraper.quit()
        
        output_path = os.path.join("f1_circuit_data", f"f1_circuits_{YEAR_TO_SCRAPE}.csv")
        save_to_csv(all_circuits_data, output_path)

    end_time = time.time()
    print("\n" + "="*40)
    print(f"Scraping terminé ! Temps total : {end_time - start_time:.2f} secondes.")
    print("="*40)
