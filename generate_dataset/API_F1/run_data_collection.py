import pandas as pd
import numpy as np
import fastf1 as ff1
import time
import random
import os

# ==============================================================================
# 1. CONFIGURATION DU CACHE
# ==============================================================================
cache_path = 'f1_cache'
if not os.path.exists(cache_path):
    os.makedirs(cache_path)
ff1.Cache.enable_cache(cache_path)

# ==============================================================================
# 2. FONCTIONS D'EXTRACTION (les versions les plus robustes que nous ayons créées)
# ==============================================================================

def load_session_with_retry(year, event_name, session_identifier, max_retries=5):
    """
    Charge une session avec une logique de relance ultra-patiente.
    """
    # ## DÉLAI DE BASE AUGMENTÉ ##
    base_delay = 20  # On commence à attendre 20 secondes en cas d'échec
    for attempt in range(max_retries):
        try:
            session = ff1.get_session(year, event_name, session_identifier)
            session.load()
            if session.laps.empty and 'FP' in session_identifier:
                raise ValueError(f"Session {session_identifier} chargée mais les données de tours sont vides.")
            return session
        except Exception as e:
            if "does not exist for this event" in str(e): return None
            wait_time = base_delay * (2 ** attempt) + random.uniform(0, 5)
            print(f"  AVERTISSEMENT: Échec pour '{year} {event_name} {session_identifier}'... Erreur: {e}")
            if attempt + 1 < max_retries:
                print(f"  Nouvelle tentative dans {wait_time:.0f} secondes...")
                time.sleep(wait_time)
            else:
                print(f"  ERREUR FINALE: Toutes les tentatives ont échoué pour '{year} {event_name} {session_identifier}'.")
                return None

def extract_maximum_features(year, event):
    """
    Fonction principale d'extraction de features.
    """
    try:
        if event['EventFormat'] == 'sprint':
            sessions_to_load = ['FP1', 'Q', 'R']
        else:
            sessions_to_load = ['FP1', 'FP2', 'FP3', 'Q', 'R']
        sessions = {name: load_session_with_retry(year, event.EventName, name) for name in sessions_to_load}
        if not sessions.get('R') or not sessions.get('Q'): return None
        
        race_results = sessions['R'].results
        if race_results.empty: return None

        df = race_results[['DriverNumber', 'TeamName', 'GridPosition', 'Position', 'FullName']].copy()
        
        # Le reste de la logique d'extraction est ici...
        # (J'inclus le code complet pour être sûr que rien ne manque)
        quali_results = sessions['Q'].results
        if 'Q3' in quali_results.columns and not quali_results['Q3'].isnull().all():
            pole_time = quali_results['Q3'].min()
            df = df.merge(quali_results[['DriverNumber', 'Abbreviation', 'Q3']], on='DriverNumber', how='left')
            df['Q3'] = pd.to_timedelta(df['Q3'])
            df['GapToPole_ms'] = (df['Q3'] - pole_time).dt.total_seconds() * 1000
        
        laps_to_concat = [s.laps for s in sessions.values() if s and 'FP' in s.name and not s.laps.empty]
        if laps_to_concat:
            fp_laps = pd.concat(laps_to_concat, ignore_index=True).pick_accurate()
            if not fp_laps.empty:
                fp_best_laps = fp_laps.groupby('DriverNumber')['LapTime'].min().reset_index().rename(columns={'LapTime': 'FP_Best_LapTime'})
                df = df.merge(fp_best_laps, on='DriverNumber', how='left')
                df['FP_Best_LapTime'] = pd.to_timedelta(df['FP_Best_LapTime']).dt.total_seconds() * 1000

        # Ajouter d'autres features ici si nécessaire...
        df['Year'] = year
        df['EventName'] = event.EventName
        
        for col in df.select_dtypes(include=np.number).columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())
        
        return df

    except Exception as e:
        print(f"  ERREUR INATTENDUE dans extract_maximum_features pour {year} {event.EventName}: {e}")
        return None

# ==============================================================================
# 3. BOUCLE DE COLLECTE PRINCIPALE (ULTRA-PATIENTE)
# ==============================================================================
if __name__ == "__main__":
    print("Lancement de la collecte de données en mode ultra-patient. Durée estimée : plusieurs heures.")

    YEARS = [2022, 2023, 2024]
    for year in YEARS:
        output_filename = f'f1_features_{year}.csv'
        if os.path.exists(output_filename):
            print(f"--- Fichier '{output_filename}' déjà existant. Passage à l'année {year+1}. ---")
            continue

        print(f"--- Traitement de la saison {year} ---")
        
        schedule = ff1.get_event_schedule(year, backend='ergast')
        now_naive = pd.to_datetime('2025-12-31').tz_localize(None)
        races_to_process = schedule[schedule['EventDate'] < now_naive]
        
        year_features = []
        for _, event in races_to_process.iterrows():
            if "Pre-Season" in event['EventName']: continue
            
            print(f"Extraction des données pour : {year} {event.EventName}...")
            race_df = extract_maximum_features(year, event)
            if race_df is not None:
                year_features.append(race_df)
            
            # ## PAUSE PRINCIPALE AUGMENTÉE ##
            sleep_time = random.uniform(20, 45) # Pause très longue entre 20 et 45 secondes
            print(f"   >>> Pause longue de {sleep_time:.0f} secondes...")
            time.sleep(sleep_time)

        if year_features:
            year_df = pd.concat(year_features, ignore_index=True)
            print(f"***** SAUVEGARDE de l'année {year} dans '{output_filename}' *****")
            year_df.to_csv(output_filename, index=False)

    print("\n--- Collecte de données par année terminée. Assemblage final... ---")
    
    all_files = [f'f1_features_{y}.csv' for y in YEARS if os.path.exists(f'f1_features_{y}.csv')]
    if all_files:
        final_df_max = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
        final_df_max.to_csv('f1_max_features_dataset.csv', index=False)
        print("Dataset final 'f1_max_features_dataset.csv' créé avec succès !")