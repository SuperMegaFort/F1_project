# live_weekend_scraper.py
import sys
import os
from config import LIVE_DATA_DIR
# IMPORTANT: Vous devez importer VOS propres fonctions de scraping ici
from f1_crawler import get_rendered_html_selenium, parse_results_table, save_to_csv

SESSIONS_TO_SCRAPE = {
    # 'session_name_in_url': ('nom_fichier_sortie.csv', {mapping_colonnes})
    "practice-1": ('practice_1.csv', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap_time': 4, 'gap': 5, 'laps': 6}),
    "practice-2": ('practice_2.csv', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap_time': 4, 'gap': 5, 'laps': 6}),
    "practice-3": ('practice_3.csv', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap_time': 4, 'gap': 5, 'laps': 6}),
    "qualifying": ('qualifying.csv', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'q1_time': 4, 'q2_time': 5, 'q3_time': 6, 'laps': 7}),
    "starting-grid": ('starting_grid.csv', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'sg_time': 4})
}

def scrape_weekend_data(year, race_name_for_url):
    print(f"--- Lancement du scraping live pour {race_name_for_url} {year} ---")
    
    # Vider le dossier des données live précédentes
    if LIVE_DATA_DIR.exists():
        for f in LIVE_DATA_DIR.glob('*.csv'):
            f.unlink()

    for session_url_part, (output_filename, col_map) in SESSIONS_TO_SCRAPE.items():
        # Vous devez construire l'URL exacte. C'est la partie la plus complexe.
        # Elle ressemble à : "https://www.formula1.com/en/results.html/{year}/races/{race_id}/{circuit_name}/{session_url_part}.html"
        # Pour cet exemple, nous allons simplifier.
        url = f"https://www.formula1.com/en/results.html/{year}/races/1234/{race_name_for_url}/{session_url_part}.html" # URL à adapter
        
        print(f"Scraping de : {url}")
        html_content = get_rendered_html_selenium(url, "table.resultsarchive-table")
        
        if html_content:
            data = parse_results_table(html_content, url, session_url_part, col_map)
            save_to_csv(data, str(LIVE_DATA_DIR / output_filename))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python live_weekend_scraper.py <année> <nom_de_la_course_pour_url>")
        sys.exit(1)
    scrape_weekend_data(sys.argv[1], sys.argv[2])
