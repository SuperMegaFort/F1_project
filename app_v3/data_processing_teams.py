# data_processing_teams.py
import pandas as pd
import fastf1 as ff1
import os
from pathlib import Path
from datetime import datetime
import pytz # Pour gérer les fuseaux horaires

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
# Chemin vers votre cache FastF1
CACHE_PATH = '/Users/cyriltelley/Desktop/MSE/Second_semester/MA-WEM/project /F1_project/app_v2/f1_cache' 

# Définition du dossier de sortie
DATA_DIR = Path("data_historical") 
OUTPUT_FILE = DATA_DIR / 'teams_summary_data.csv'

# On inclut 2025 pour traiter les données en cours de saison
YEARS_TO_PROCESS = [2020, 2021, 2022, 2023, 2024, 2025]

# ==============================================================================
# 2. SCRIPT DE TRAITEMENT
# ==============================================================================
def generate_team_summary():
    """
    Lit les données de course depuis le cache FastF1, agrège les points par pilote
    et par écurie pour chaque année, et sauvegarde le tout dans un unique CSV.
    Cette version ne traite que les courses déjà passées.
    """
    if not os.path.exists(CACHE_PATH):
        print(f"❌ ERREUR: Le dossier cache '{CACHE_PATH}' est introuvable.")
        print("Veuillez vérifier le chemin dans le script.")
        return

    print(f"Activation du cache FastF1 à l'emplacement : {CACHE_PATH}")
    ff1.Cache.enable_cache(CACHE_PATH)

    all_years_data = []
    
    # Obtenir la date et l'heure actuelles avec le fuseau horaire UTC pour une comparaison fiable
    now_utc = datetime.now(pytz.utc)

    for year in YEARS_TO_PROCESS:
        print(f"--- Traitement de l'année {year} ---")
        try:
            schedule = ff1.get_event_schedule(year, include_testing=False)
            
            # CORRECTION : On localise les dates en UTC au lieu d'essayer de les convertir
            schedule['EventDate'] = pd.to_datetime(schedule['EventDate']).dt.tz_localize('UTC')
            
            # FILTRER LES COURSES PASSÉES UNIQUEMENT
            races_to_process = schedule[schedule['EventDate'] < now_utc]
            
            if races_to_process.empty:
                 print(f"  Aucune course passée trouvée pour l'année {year}. Passage à l'année suivante.")
                 continue
            
        except Exception as e:
            print(f"  Impossible de charger le calendrier pour {year}. Erreur : {e}")
            continue
            
        season_results = []
        for _, event in races_to_process.iterrows():
            try:
                session = ff1.get_session(year, event.EventName, 'R')
                session.load(telemetry=False, weather=False, messages=False, laps=False) # Optimisation
                results = session.results
                
                if results is not None and not results.empty:
                    season_results.append(results)
                else:
                    print(f"  Pas de résultats pour {year} {event.EventName}")

            except Exception as e:
                print(f"  Impossible de charger la session pour {year} {event.EventName}: {e}")
                continue
        
        if not season_results:
            print(f"Aucune donnée de résultat de course agrégée pour {year}.")
            continue

        year_df = pd.concat(season_results, ignore_index=True)
        
        year_df['Points'] = pd.to_numeric(year_df['Points'], errors='coerce').fillna(0)

        driver_points = year_df.groupby(['TeamName', 'FullName', 'Abbreviation'])['Points'].sum().reset_index()
        driver_points = driver_points[driver_points['Points'] >= 0]
        
        team_points = year_df.groupby('TeamName')['Points'].sum().reset_index()
        team_points.rename(columns={'Points': 'TeamPoints'}, inplace=True)
        
        merged_data = pd.merge(driver_points, team_points, on='TeamName', how='left')
        merged_data['Year'] = year
        
        all_years_data.append(merged_data)

    if all_years_data:
        final_df = pd.concat(all_years_data, ignore_index=True)
        
        final_df = final_df[['Year', 'TeamName', 'TeamPoints', 'FullName', 'Abbreviation', 'Points']]
        final_df.rename(columns={'Points': 'DriverPoints', 'FullName': 'DriverName'}, inplace=True)
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Fichier récapitulatif des écuries sauvegardé avec succès dans : {OUTPUT_FILE}")
    else:
        print("\n❌ Aucune donnée n'a pu être traitée. Le fichier de sortie n'a pas été créé.")

if __name__ == "__main__":
    generate_team_summary()
