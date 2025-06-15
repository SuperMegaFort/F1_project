# crawler_pilote_standard_selenium.py
# -*- coding: utf-8 -*-
# ATTENTION : Ce script utilise Selenium standard et risque d'être bloqué par le site F1.
# Il est adapté pour suivre l'architecture de crawler_prediction.py.

import time
import csv
import os
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
DRIVERS_PAGE_URL = f"{BASE_URL}/en/drivers.html"
OUTPUT_DIR = "f1_driver_data"
OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, "f1_drivers_all.csv")
WAIT_SECONDS = 15 # Temps d'attente pour le chargement initial de la page

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

def get_driver_urls(driver, overview_url):
    """Navigue vers la page principale et extrait les URLs des pages de détail des pilotes."""
    print(f"Navigation vers : {overview_url}")
    try:
        driver.get(overview_url)
        print(f"Attente de {WAIT_SECONDS} secondes pour le chargement...")
        # NOTE : Une attente explicite est souvent nécessaire pour les pages complexes
        WebDriverWait(driver, WAIT_SECONDS).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/en/drivers/"]'))
        )
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        links = soup.select('a[href*="/en/drivers/"]')
        if not links:
            print("!!! Aucun lien de pilote trouvé.")
            return []

        unique_urls = set()
        for link in links:
            href = link.get('href', '')
            if href and href.strip() not in ['/en/drivers.html', '/en/drivers']:
                full_url = urljoin(overview_url, href)
                unique_urls.add(full_url)
        
        urls = sorted(list(unique_urls))
        print(f"-> {len(urls)} URLs de pilotes uniques trouvées.")
        return urls
    except TimeoutException:
        print("!!! TIMEOUT: Le contenu de la page des pilotes n'a pas chargé à temps.")
        return []
    except Exception as e:
        print(f"!!! Une erreur est survenue lors de la récupération des URLs : {type(e).__name__} - {e}")
        return []

def parse_driver_page(html_content, url):
    """Extrait les informations d'un pilote depuis le code HTML de sa page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    driver_data = {'url': url}

    def get_safe_text(element): return element.get_text(strip=True) if element else 'N/A'
    def get_safe_src(element): return element.get('src', '') if element else ''
    
    driver_data['full_name'] = get_safe_text(soup.select_one("h1.f1-heading__body"))
    
    number_container = soup.select_one(".f1-driver-position p.f1-heading")
    driver_data['driver_number'] = number_container.get_text(strip=True).split(' ')[0] if number_container else 'N/A'
    
    driver_data['main_image_url'] = get_safe_src(soup.select_one("img.f1-c-image.aspect-square"))

    stats_mapping = {
        'Team': 'team', 'Country': 'country', 'Podiums': 'podiums', 'Points': 'points', 
        'Grands Prix entered': 'grands_prix_entered', 'World Championships': 'world_championships', 
        'Highest race finish': 'highest_race_finish', 'Highest grid position': 'highest_grid_position', 
        'Date of birth': 'date_of_birth', 'Place of birth': 'place_of_birth'
    }
    
    stats_list = soup.select_one("dl.f1-grid")
    if stats_list:
        for label_dt in stats_list.find_all('dt'):
            label_text = label_dt.get_text(strip=True)
            if label_text in stats_mapping:
                value_dd = label_dt.find_next_sibling('dd')
                driver_data[stats_mapping[label_text]] = get_safe_text(value_dd)
    
    return driver_data

def save_to_csv(data, filename):
    """Sauvegarde les données collectées dans un fichier CSV."""
    if not data:
        print("Aucune donnée à sauvegarder.")
        return
    print(f"\nSauvegarde de {len(data)} pilotes dans {filename}...")
    headers = [
        'full_name', 'driver_number', 'team', 'country', 'podiums', 'points',
        'grands_prix_entered', 'world_championships', 'highest_race_finish',
        'highest_grid_position', 'date_of_birth', 'place_of_birth', 
        'main_image_url', 'url'
    ]
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"-> Données sauvegardées avec succès.")

# --- FONCTION PRINCIPALE (ORCHESTRATEUR) ---
def run_pilots_crawler():
    """Orchestre le processus complet de scraping des pilotes."""
    driver = setup_driver()
    if not driver:
        return

    try:
        urls_to_scrape = get_driver_urls(driver, DRIVERS_PAGE_URL)
        
        if not urls_to_scrape:
            print("Aucune URL à scraper. Arrêt du script.")
            return

        all_data = []
        for url in urls_to_scrape:
            print(f"--- Traitement de : {url}")
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.f1-heading__body")))
                html = driver.page_source
                parsed_data = parse_driver_page(html, url)
                
                if parsed_data and parsed_data.get('full_name', 'N/A') != 'N/A':
                    all_data.append(parsed_data)
                    print(f"-> Données extraites pour {parsed_data['full_name']}")
                else:
                    print(f"-> Nom du pilote non trouvé, données ignorées.")
            except Exception as e:
                print(f"!!! Erreur lors du scraping de la page {url}: {e}")

        save_to_csv(all_data, OUTPUT_FILENAME)

    finally:
        if driver:
            driver.quit()
            print("\nNavigateur fermé.")

# --- POINT D'ENTRÉE DU SCRIPT ---
if __name__ == "__main__":
    print("="*40)
    print(" Lancement du Crawler F1 - Pilotes (Selenium Standard)")
    print("="*40)
    start_time = time.time()
    
    run_pilots_crawler()
    
    end_time = time.time()
    print("\n" + "="*40)
    print(f"Scraping terminé ! Temps total : {end_time - start_time:.2f} secondes.")
    print("="*40)
