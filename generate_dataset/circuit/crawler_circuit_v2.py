# crawler_circuits_standard_selenium.py
# -*- coding: utf-8 -*-
# ATTENTION : Ce script utilise Selenium standard et risque d'être bloqué par le site F1.
# Il est adapté pour suivre l'architecture de crawler_prediction.py.

import time
import csv
import os
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Importations de Selenium Standard ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# --- CONFIGURATION & CONSTANTES ---
BASE_URL = "https://www.formula1.com"
YEAR_TO_SCRAPE = 2024
SEASON_PAGE_URL = f"{BASE_URL}/en/racing/{YEAR_TO_SCRAPE}.html"
OUTPUT_DIR = "f1_circuit_data"
OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, f"f1_circuits_{YEAR_TO_SCRAPE}.csv")
WAIT_SECONDS = 10

# Dictionnaires manuels (pour les images et le mapping)
circuits_manual_image_data = {
    'bahrain': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Bahrain_Circuit.png', 'jeddah': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Saudi_Arabia_Circuit.png',
    'albert_park': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Australia_Circuit.png', 'baku': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Baku_Circuit.png',
    'shanghai': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/China_Circuit.png', 'miami': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Miami_Circuit.png',
    'imola': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Emilia_Romagna_Circuit.png', 'monaco': 'https://media.formula1.com/image/upload/f_auto,c_limit,q_auto,w_1320/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Monaco_Circuit',
    'villeneuve': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Canada_Circuit.png', 'catalunya': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Spain_Circuit.png',
    'red_bull_ring': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Austria_Circuit.png', 'silverstone': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Great_Britain_Circuit.png',
    'hungaroring': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Hungary_Circuit.png', 'spa': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Belgium_Circuit.png',
    'zandvoort': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Netherlands_Circuit.png', 'monza': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Italy_Circuit.png',
    'marina_bay': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Singapore_Circuit.png', 'suzuka': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Japan_Circuit.png',
    'losail': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Qatar_Circuit.png', 'americas': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/USA_Circuit.png',
    'rodriguez': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Mexico_Circuit.png', 'interlagos': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Brazil_Circuit.png',
    'vegas': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Las_Vegas_Circuit.png', 'yas_marina': 'https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Abu_Dhabi_Circuit.png',
}
URL_SLUG_TO_CIRCUIT_ID = {
    'bahrain': 'bahrain', 'saudi-arabia': 'jeddah', 'australia': 'albert_park', 'japan': 'suzuka', 'china': 'shanghai',
    'miami': 'miami', 'emiliaromagna': 'imola', 'monaco': 'monaco', 'canada': 'villeneuve', 'spain': 'catalunya',
    'austria': 'red_bull_ring', 'great-britain': 'silverstone', 'hungary': 'hungaroring', 'belgium': 'spa',
    'netherlands': 'zandvoort', 'italy': 'monza', 'azerbaijan': 'baku', 'singapore': 'marina_bay',
    'united-states': 'americas', 'mexico': 'rodriguez', 'brazil': 'interlagos', 'las-vegas': 'vegas',
    'qatar': 'losail', 'abudhabi': 'yas_marina', 'united-arab-emirates': 'yas_marina'
}


# --- FONCTIONS UTILITAIRES ---

def setup_driver():
    """Configure et retourne une instance de Selenium standard."""
    print("Initialisation du navigateur Selenium standard...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"!!! Erreur lors de l'initialisation du driver : {e}")
        return None

def parse_circuit_page(html_content, url):
    """Extrait les informations d'un circuit depuis le code HTML de sa page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    circuit_data = {'url': url}
    
    def get_safe_text(element): return element.get_text(strip=True) if element else 'N/A'
    def get_safe_src(element): return element.get('src', '') if element else ''

    circuit_data['circuit_name'] = get_safe_text(soup.select_one("h2.f1-heading__body div"))
    circuit_data['country_flag_url'] = get_safe_src(soup.select_one("img[alt$='-flag.png']"))

    try:
        slug = urlparse(url).path.split('/')[-2]
        circuit_id = URL_SLUG_TO_CIRCUIT_ID.get(slug)
        circuit_data['image_url'] = circuits_manual_image_data.get(circuit_id, '') if circuit_id else ''
    except Exception:
        circuit_data['image_url'] = ''

    stats_mapping = {
        'First Grand Prix': 'first_gp', 'Number of Laps': 'laps',
        'Circuit Length': 'length_km', 'Race Distance': 'race_distance_km',
        'Lap Record': 'lap_record_time'
    }
    for container in soup.select("div.f1-grid > div[class*='border-']"):
        label = get_safe_text(container.select_one("span.f1-text"))
        value_element = container.select_one("h2.f1-heading")
        if label in stats_mapping and value_element:
            value = value_element.find(string=True, recursive=False).strip()
            circuit_data[stats_mapping[label]] = value
            if label == 'Lap Record':
                driver_span = value_element.select_one("span.f1-text")
                circuit_data['lap_record_driver'] = get_safe_text(driver_span).replace('(','').replace(')','')

    return circuit_data

def save_to_csv(data, filename):
    """Sauvegarde les données collectées dans un fichier CSV."""
    if not data:
        print("Aucune donnée à sauvegarder.")
        return
    print(f"\nSauvegarde de {len(data)} circuits dans {filename}...")
    headers = [
        'circuit_name', 'length_km', 'laps', 'race_distance_km', 'first_gp', 
        'lap_record_time', 'lap_record_driver', 'image_url', 'country_flag_url', 'url'
    ]
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"-> Données sauvegardées avec succès.")


# --- FONCTION PRINCIPALE (ORCHESTRATEUR) ---

def run_circuits_crawler(driver, season_url):
    """Orchestre le processus de scraping des circuits pour une saison."""
    try:
        # Étape 1: Obtenir les URLs des courses
        print(f"Navigation vers la page de la saison : {season_url}")
        driver.get(season_url)
        WebDriverWait(driver, WAIT_SECONDS).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.group[href*='/racing/']")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        race_links = [urljoin(season_url, a['href']) for a in soup.select("a.group[href*='/racing/']") if 'testing' not in a['href']]
        unique_race_urls = sorted(list(set(race_links)))
        print(f"-> {len(unique_race_urls)} URLs de courses trouvées.")

        # Étape 2: Obtenir les URLs de détail des circuits
        circuit_detail_urls = set()
        for url in unique_race_urls:
            print(f"  - Analyse de la course : {url}")
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='/circuit']")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            circuit_link = soup.select_one("a[href$='/circuit']")
            if circuit_link:
                circuit_detail_urls.add(urljoin(url, circuit_link['href']))
        
        urls_to_scrape = sorted(list(circuit_detail_urls))
        if not urls_to_scrape:
            print("Aucune URL de circuit à scraper. Arrêt.")
            return

        print(f"\n-> {len(urls_to_scrape)} URLs de circuits uniques à scraper.")

        # Étape 3: Scraper chaque page de circuit
        all_data = []
        for url in urls_to_scrape:
            print(f"--- Traitement de : {url}")
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.f1-heading__body")))
            parsed_data = parse_circuit_page(driver.page_source, url)
            if parsed_data and parsed_data.get('circuit_name', 'N/A') not in ['N/A', '']:
                all_data.append(parsed_data)
                print(f"-> Données extraites pour {parsed_data['circuit_name']}")
            else:
                print(f"-> Nom du circuit non trouvé, données ignorées.")
        
        save_to_csv(all_data, OUTPUT_FILENAME)

    except Exception as e:
        print(f"!!! Une erreur est survenue pendant le scraping : {e}")

# --- POINT D'ENTRÉE DU SCRIPT ---

if __name__ == "__main__":
    print("="*40)
    print(f" Lancement du Crawler F1 - Circuits (Saison {YEAR_TO_SCRAPE})")
    print("="*40)
    start_time = time.time()
    
    driver = setup_driver()
    if driver:
        try:
            run_circuits_crawler(driver, SEASON_PAGE_URL)
        finally:
            driver.quit()
            print("\nNavigateur fermé.")
            
    end_time = time.time()
    print("\n" + "="*40)
    print(f"Scraping terminé ! Temps total : {end_time - start_time:.2f} secondes.")
    print("="*40)
