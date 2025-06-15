import pandas as pd
import numpy as np
import fastf1 as ff1
import time
import random

# ==============================================================================
# FONCTION 1 : Le chargeur de session robuste (inchangé)
# ==============================================================================
def load_session_with_retry(year, event_name, session_identifier):
    """Charge une session avec une logique de relance robuste."""
    try:
        session = ff1.get_session(year, event_name, session_identifier)
        session.load()
        # On ne considère pas une session d'essais vide comme une erreur, on retourne simplement None
        if session.laps.empty and 'FP' in session_identifier:
            return None
        return session
    except Exception as e:
        # Si la session n'existe pas (ex: FP3 pour un sprint), ce n'est pas une erreur à retenter
        if "does not exist for this event" in str(e):
            return None
        # Pour les autres erreurs (réseau...), on peut logger mais on retourne None pour ne pas bloquer
        # print(f"  AVERTISSEMENT: Échec du chargement pour '{year} {event_name} {session_identifier}'. Erreur: {e}")
        return None


# ==============================================================================
# FONCTION 2 : L'extracteur de features (VERSION FINALE ET COMPLÈTE)
# ==============================================================================
def extract_maximum_features(year, event):
    """
    Version finale et complète qui calcule toutes les features requises.
    """
    try:
        # --- 1. Chargement des Sessions du Weekend ---
        if event['EventFormat'] == 'sprint':
            sessions_to_load = ['FP1', 'Q', 'R']
        else:
            sessions_to_load = ['FP1', 'FP2', 'FP3', 'Q', 'R']
        sessions = {name: load_session_with_retry(year, event.EventName, name) for name in sessions_to_load}
        if not all(sessions.get(s) for s in ['R', 'Q']): 
            print(f"Données de Course ou de Qualif manquantes pour {event.EventName}")
            return None
        
        race_results = sessions['R'].results
        if race_results.empty: return None

        df = race_results[['DriverNumber', 'TeamName', 'GridPosition', 'Position', 'FullName', 'Status']].copy()
        
        # --- 2. Features de Pré-Course ---
        quali_results = sessions['Q'].results
        time_cols = [col for col in ['Q1', 'Q2', 'Q3'] if col in quali_results.columns]
        for col in time_cols:
            quali_results[col] = pd.to_timedelta(quali_results[col], errors='coerce')
        
        if time_cols:
            quali_results['BestQualiTime'] = quali_results[time_cols].min(axis=1)
            if not quali_results['BestQualiTime'].isnull().all():
                df = df.merge(quali_results[['DriverNumber', 'Abbreviation', 'BestQualiTime']], on='DriverNumber', how='left')
                pole_time = df['BestQualiTime'].min()
                df['GapToPole_ms'] = (df['BestQualiTime'] - pole_time).dt.total_seconds() * 1000
                teammate_best_time = df.groupby('TeamName')['BestQualiTime'].transform('min')
                df['GapToTeammate_ms'] = (df['BestQualiTime'] - teammate_best_time).dt.total_seconds() * 1000

        fp_laps_list = [s.laps.pick_accurate() for s in sessions.values() if s and 'FP' in s.name and not s.laps.empty]
        if fp_laps_list:
            fp_laps = pd.concat(fp_laps_list, ignore_index=True)
            if not fp_laps.empty:
                fp_best = fp_laps.groupby('DriverNumber')['LapTime'].min().reset_index()
                df = df.merge(fp_best.rename(columns={'LapTime': 'FP_Best_LapTime'}), on='DriverNumber', how='left')
                df['FP_Best_LapTime'] = pd.to_timedelta(df['FP_Best_LapTime']).dt.total_seconds() * 1000
                df['FP_Rank'] = df['FP_Best_LapTime'].rank(method='min')

        # --- 3. Features de Saison et d'Historique ---
        current_round = event.RoundNumber
        drivers_points, constructors_points, recent_form_points, dnf_counts = {}, {}, {}, {}
        
        for i in range(1, current_round):
            prev_race = load_session_with_retry(year, i, 'R')
            if prev_race and not prev_race.results.empty:
                for _, row in prev_race.results.iterrows():
                    d_num, t_name, pts, status = row['DriverNumber'], row['TeamName'], row['Points'], row['Status']
                    drivers_points[d_num] = drivers_points.get(d_num, 0) + pts
                    constructors_points[t_name] = constructors_points.get(t_name, 0) + pts
                    if current_round - i <= 3:
                        recent_form_points[d_num] = recent_form_points.get(d_num, 0) + pts
                    if 'Finished' not in status and '+' not in status:
                        dnf_counts[d_num] = dnf_counts.get(d_num, 0) + 1
        
        df['Driver_Championship_Points'] = df['DriverNumber'].map(drivers_points).fillna(0)
        df['Constructor_Championship_Points'] = df['TeamName'].map(constructors_points).fillna(0)
        df['Driver_Recent_Form_Points'] = df['DriverNumber'].map(recent_form_points).fillna(0)
        df['Driver_DNF_Count_Season'] = df['DriverNumber'].map(dnf_counts).fillna(0)
        
        # --- BLOC DE CODE QUI MANQUAIT : HISTORIQUE SUR LE CIRCUIT ---
        driver_history_pos = []
        for d_num in df['DriverNumber']:
            positions = []
            for y in range(year - 2, year):
                past_race_session = load_session_with_retry(y, event.EventName, 'R')
                if past_race_session and not past_race_session.results.empty:
                    driver_past_result = past_race_session.results.loc[past_race_session.results['DriverNumber'] == d_num]
                    if not driver_past_result.empty:
                        positions.append(driver_past_result['Position'].iloc[0])
            driver_history_pos.append(np.mean(positions) if positions else np.nan)
        df['Driver_Circuit_History_AvgPos'] = driver_history_pos

        # --- 4. Nettoyage Final ---
        df['Year'] = year
        df['EventName'] = event.EventName
        
        # Remplacer les NaN restants par la médiane de la colonne
        for col in df.select_dtypes(include=np.number).columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())
        
        return df

    except Exception as e:
        print(f"ERREUR FINALE DANS L'EXTRACTION pour {year} {event.EventName}: {e}")
        # Afficher le traceback complet pour le debug
        import traceback
        traceback.print_exc()
        return None