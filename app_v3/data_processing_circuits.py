# data_processing_circuits.py

import pandas as pd
import fastf1 as ff1
import ergast_py
from datetime import datetime
import os # <-- 1. IMPORTATION NÉCESSAIRE

# --- Données Manuelles Enrichies ---
# (Ce dictionnaire est correct et reste inchangé)
circuits_manual_data = {
    'bahrain': {'corners': 15, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/2/29/Bahrain_International_Circuit--2020.svg', 'fastf1_name': 'Bahrain'},
    'jeddah': {'corners': 27, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/3/3c/Jeddah_Street_Circuit_2023.svg', 'fastf1_name': 'Saudi Arabia'},
    'albert_park': {'corners': 14, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/3/31/Albert_Park_Circuit_2023.svg', 'fastf1_name': 'Australia'},
    'baku': {'corners': 20, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/e/e3/Baku_City_Circuit_2023.svg', 'fastf1_name': 'Azerbaijan'},
    'miami': {'corners': 19, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/f/f3/Miami_International_Autodrome.svg', 'fastf1_name': 'Miami'},
    'imola': {'corners': 19, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/3/34/Imola_2009.svg', 'fastf1_name': 'Emilia Romagna'},
    'monaco': {'corners': 19, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/3/36/Circuit_de_Monaco_2021_Layout.svg', 'fastf1_name': 'Monaco'},
    'catalunya': {'corners': 14, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/2/20/Circuit_de_Catalunya_2023_grand_prix_layout.svg', 'fastf1_name': 'Spain'},
    'villeneuve': {'corners': 14, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/d/d0/Circuit_Gilles_Villeneuve_2017.svg', 'fastf1_name': 'Canada'},
    'red_bull_ring': {'corners': 10, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/b/b2/Red_Bull_Ring.svg', 'fastf1_name': 'Austria'},
    'silverstone': {'corners': 18, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/c/ca/Silverstone_Circuit_2022_Grand_Prix_Layout.svg', 'fastf1_name': 'Great Britain'},
    'hungaroring': {'corners': 14, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/9/91/Hungaroring.svg', 'fastf1_name': 'Hungary'},
    'spa': {'corners': 19, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/5/54/Spa-Francorchamps_of_Belgium_2020.svg', 'fastf1_name': 'Belgium'},
    'zandvoort': {'corners': 14, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/5/58/Zandvoort_2022.svg', 'fastf1_name': 'Netherlands'},
    'monza': {'corners': 11, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Monza_layout.svg', 'fastf1_name': 'Italy'},
    'marina_bay': {'corners': 19, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/d/d4/Marina_Bay_Street_Circuit_2023.svg', 'fastf1_name': 'Singapore'},
    'suzuka': {'corners': 18, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/e/e5/Suzuka_circuit_map--2005.svg', 'fastf1_name': 'Japan'},
    'losail': {'corners': 16, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Losail_International_Circuit_2021.svg', 'fastf1_name': 'Qatar'},
    'americas': {'corners': 20, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Circuit_of_the_Americas_2019.svg', 'fastf1_name': 'United States'},
    'rodriguez': {'corners': 17, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/5/54/Aut%C3%B3dromo_Hermanos_Rodr%C3%ADguez_2015.svg', 'fastf1_name': 'Mexico City'},
    'interlagos': {'corners': 15, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/b/be/Interlagos_2022.svg', 'fastf1_name': 'Brazil'},
    'vegas': {'corners': 17, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/5/56/Las_Vegas_Strip_Circuit.svg', 'fastf1_name': 'Las Vegas'},
    'yas_marina': {'corners': 16, 'imageUrl': 'https://upload.wikimedia.org/wikipedia/commons/d/d1/Yas_Marina_Circuit_2021.svg', 'fastf1_name': 'Abu Dhabi'},
}

def get_recent_fastest_lap(fastf1_event_name):
    """Trouve le meilleur tour pour un circuit en se basant sur le nom de l'événement FastF1."""
    current_year = datetime.now().year
    for year in range(current_year, 2018, -1):
        try:
            print(f"  -> Recherche de l'événement '{fastf1_event_name}' pour l'année {year}...")
            
            # <-- 2. CRÉATION DU DOSSIER CACHE SI NÉCESSAIRE
            cache_dir = 'cache'
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            ff1.Cache.enable_cache(cache_dir)
            
            session = ff1.get_session(year, fastf1_event_name, 'R')
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            
            fastest = session.laps.pick_fastest()
            if fastest is None:
                print(f"    ! Pas de meilleur tour trouvé pour {fastf1_event_name} en {year}.")
                continue

            lap_time = fastest['LapTime']
            driver_code = fastest['Driver']
            
            time_str = str(lap_time).split(':', 1)[1][:-3]
            
            circuit_length_km = session.get_circuit_info().length / 1000
            
            print(f"    ✓ Données trouvées pour {year} !")
            return time_str, driver_code, circuit_length_km
            
        except Exception as e:
            # On ignore les erreurs pour les années où la course n'a pas eu lieu (ex: 2025)
            if "No data for" not in str(e):
                 print(f"    ! Erreur non critique pour {fastf1_event_name} en {year}: {e}")
            continue
            
    return None, None, None

def create_circuits_dataframe():
    """Crée un DataFrame Pandas avec les données des circuits."""
    ergast = ergast_py.Ergast()
    circuits = ergast.get_circuits()
    
    all_circuits_data = []

    for circuit in circuits:
        circuit_id = circuit.circuit_id
        
        if circuit_id not in circuits_manual_data:
            continue

        print(f"Traitement du circuit : {circuit.circuit_name} ({circuit_id})")
        
        manual_data = circuits_manual_data[circuit_id]
        
        best_lap, driver, length = get_recent_fastest_lap(manual_data['fastf1_name'])
        
        if best_lap:
            all_circuits_data.append({
                'circuitId': circuit_id,
                'circuitName': circuit.circuit_name,
                'locality': circuit.locality,
                'country': circuit.country,
                'corners': manual_data['corners'],
                'imageUrl': manual_data['imageUrl'],
                'bestLapTimeStr': best_lap,
                'bestLapDriver': driver,
                'circuitLengthKm': length
            })
        else:
            print(f"  -> Impossible de trouver des données de meilleur tour pour {circuit.circuit_name}")

    df = pd.DataFrame(all_circuits_data)
    return df

if __name__ == '__main__':
    output_filename = 'circuits_data.csv'
    circuits_df = create_circuits_dataframe()
    
    if not circuits_df.empty:
        circuits_df.to_csv(output_filename, index=False, encoding='utf-8')
        print(f"\nFichier '{output_filename}' créé avec succès avec {len(circuits_df)} circuits.")
    else:
        print(f"\nLe script s'est terminé, mais aucune donnée de circuit n'a pu être collectée. Le fichier '{output_filename}' n'a pas été modifié.")