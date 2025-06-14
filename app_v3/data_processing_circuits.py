# data_processing_circuits.py
import pandas as pd
import fastf1 as ff1
import os
from pathlib import Path

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
DATA_DIR = Path("data_historical") 
OUTPUT_FILE = DATA_DIR / 'circuits_summary_data.csv'
YEARS_TO_PROCESS = [2020, 2021, 2022, 2023, 2024]
CACHE_PATH = '/Users/cyriltelley/Desktop/MSE/Second_semester/MA-WEM/project /F1_project/app_v2/f1_cache' 

# Dictionnaire associant l'ID officiel du circuit à une URL d'image
CIRCUIT_IMAGE_MAPPING = {
    "bahrain": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Bahrain_International_Circuit--2020.svg/1920px-Bahrain_International_Circuit--2020.svg.png",
    "imola": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Autodromo_Enzo_e_Dino_Ferrari.svg/1920px-Autodromo_Enzo_e_Dino_Ferrari.svg.png",
    "portimao": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Algarve_International_Circuit_layout.svg/1920px-Algarve_International_Circuit_layout.svg.png",
    "catalunya": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Circuit_de_Barcelona-Catalunya_2021.svg/1920px-Circuit_de_Barcelona-Catalunya_2021.svg.png",
    "monaco": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Monaco_Circuit.svg/1920px-Monaco_Circuit.svg.png",
    "baku": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Baku_City_Circuit_2023.svg/1920px-Baku_City_Circuit_2023.svg.png",
    "ricard": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Paul_Ricard_2018.svg/1920px-Paul_Ricard_2018.svg.png",
    "red_bull_ring": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Red_Bull_Ring_2017.svg/1920px-Red_Bull_Ring_2017.svg.png",
    "hungaroring": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Hungaroring.svg/1920px-Hungaroring.svg.png",
    "silverstone": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Silverstone_Circuit_2020.svg/1920px-Silverstone_Circuit_2020.svg.png",
    "spa": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Spa-Francorchamps_of_Belgium.svg/1920px-Spa-Francorchamps_of_Belgium.svg.png",
    "zandvoort": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Zandvoort_2021.svg/1920px-Zandvoort_2021.svg.png",
    "monza": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Monza_track_map.svg/1920px-Monza_track_map.svg.png",
    "sochi": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Sochi_Autodrom.svg/1920px-Sochi_Autodrom.svg.png",
    "istanbul": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Istanbul_Park.svg/1920px-Istanbul_Park.svg.png",
    "americas": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Austin_circuit.svg/1920px-Austin_circuit.svg.png",
    "rodriguez": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Aut%C3%B3dromo_Hermanos_Rodr%C3%ADguez_2015.svg/1920px-Aut%C3%B3dromo_Hermanos_Rodr%C3%ADguez_2015.svg.png",
    "interlagos": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Aut%C3%B3dromo_Jos%C3%A9_Carlos_Pace.svg/1920px-Aut%C3%B3dromo_Jos%C3%A9_Carlos_Pace.svg.png",
    "jeddah": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Jeddah_Street_Circuit.svg/1920px-Jeddah_Street_Circuit.svg.png",
    "yas_marina": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Yas_Marina_Circuit_2021.svg/1920px-Yas_Marina_Circuit_2021.svg.png",
    "albert_park": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Albert_Park_Circuit_2022.svg/1920px-Albert_Park_Circuit_2022.svg.png",
    "miami": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Miami_International_Autodrome.svg/1920px-Miami_International_Autodrome.svg.png",
    "villeneuve": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bE/Circuit_Gilles_Villeneuve.svg/1920px-Circuit_Gilles_Villeneuve.svg.png",
    "marina_bay": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Singapore_Street_Circuit_2023.svg/1920px-Singapore_Street_Circuit_2023.svg.png",
    "losail": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Losail_International_Circuit_2021_layout_map.svg/1920px-Losail_International_Circuit_2021_layout_map.svg.png",
    "vegas": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Las_Vegas_Strip_Circuit.svg/1920px-Las_Vegas_Strip_Circuit.svg.png",
    "shanghai": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Shanghai_International_Racing_Circuit_track_map.svg/1920px-Shanghai_International_Racing_Circuit_track_map.svg.png",
    "suzuka" : "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Suzuka_circuit_map--2005.svg/1920px-Suzuka_circuit_map--2005.svg.png",
    "nurburgring": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/N%C3%BCrburgring_-_Grand-Prix-Strecke_2021.svg/1920px-N%C3%BCrburgring_-_Grand-Prix-Strecke_2021.svg.png",
    "mugello": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Mugello_Racing_Circuit_track_map.svg/1920px-Mugello_Racing_Circuit_track_map.svg.png"
}

# ==============================================================================
# 2. SCRIPT DE TRAITEMENT
# ==============================================================================
def generate_circuit_summary():
    """
    Génère un fichier CSV contenant les informations de base de chaque circuit par année.
    Nouvelle méthode plus robuste pour extraire les informations.
    """
    if not os.path.exists(CACHE_PATH):
        print(f"❌ ERREUR: Le dossier cache '{CACHE_PATH}' est introuvable.")
        return

    print(f"Activation du cache FastF1 à l'emplacement : {CACHE_PATH}")
    ff1.Cache.enable_cache(CACHE_PATH)
    
    all_circuits_data = []

    for year in YEARS_TO_PROCESS:
        print(f"--- Traitement des circuits pour l'année {year} ---")
        try:
            schedule = ff1.get_event_schedule(year, include_testing=False)
            
            circuits_info = []
            for round_num in schedule['RoundNumber']:
                try:
                    # Charger la session de qualification (plus légère que la course) pour obtenir les infos
                    session = ff1.get_session(year, round_num, 'Q')
                    # Pas besoin de .load() si on veut juste les métadonnées de l'événement
                    
                    circuit_id = session.event['Circuit']['circuitId']
                    
                    circuits_info.append({
                        "Year": year,
                        "EventName": session.event['EventName'],
                        "Country": session.event['Country'],
                        "Location": session.event['Location'],
                        "OfficialEventName": session.event['OfficialEventName'],
                        "CircuitId": circuit_id
                    })
                    print(f"  OK: {session.event['EventName']}")

                except Exception as e:
                    print(f"  AVERTISSEMENT: Impossible de traiter l'événement {round_num}. Erreur: {e}")
                    continue
            
            if circuits_info:
                year_df = pd.DataFrame(circuits_info)
                all_circuits_data.append(year_df)

        except Exception as e:
            print(f"  ERREUR: Impossible de charger le calendrier pour {year}. Erreur : {e}")
            continue

    if all_circuits_data:
        final_df = pd.concat(all_circuits_data, ignore_index=True).drop_duplicates()
        final_df['ImageUrl'] = final_df['CircuitId'].map(CIRCUIT_IMAGE_MAPPING).fillna('')
        final_df = final_df[['Year', 'EventName', 'Country', 'Location', 'OfficialEventName', 'ImageUrl']]
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Fichier récapitulatif des circuits sauvegardé avec succès dans : {OUTPUT_FILE}")
    else:
        print("\n❌ Aucune donnée de circuit n'a pu être traitée.")

if __name__ == "__main__":
    generate_circuit_summary()
