# feature_engineering.py
import pandas as pd
import numpy as np

def convert_laptime_to_ms(lap_time):
    """
    Convertit un temps au tour du format 'MM:SS.ms' ou 'HH:MM:SS.ms' en millisecondes.
    Retourne NaN si le format est invalide.
    """
    if pd.isna(lap_time) or not isinstance(lap_time, str):
        return np.nan
    try:
        parts = lap_time.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds_part = parts[1].split('.')
            seconds = int(seconds_part[0])
            ms = int(seconds_part[1]) if len(seconds_part) > 1 else 0
            total_seconds = minutes * 60 + seconds
        elif len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_part = parts[2].split('.')
            seconds = int(seconds_part[0])
            ms = int(seconds_part[1]) if len(seconds_part) > 1 else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
        else:
            return np.nan
            
        return total_seconds * 1000 + ms
    except (ValueError, IndexError):
        return np.nan

def create_features(full_historical_df, race_weekend_data):
    """
    Crée le jeu de features pour une course en combinant données historiques et du week-end.
    Version mise à jour avec driver_number et une logique d'historique circuit améliorée.
    """
    df = race_weekend_data.copy()

    # --- Initialisation des colonnes ---
    base_feature_cols = [
        'driver_number', # Ajout du numéro de pilote comme feature
        'GapToPole_ms', 'FP_Best_LapTime_s', 'FP_Rank',
        'Driver_Championship_Points', 'Constructor_Championship_Points',
        'Driver_DNF_Count_Season', 'Driver_Circuit_History_AvgPos',
        'year_weight'
    ]
    for col in base_feature_cols:
        if col not in df.columns:
            df[col] = np.nan

    # --- 1. Features de Qualification ---
    q_cols_ms = []
    for col in ['q1_time', 'q2_time', 'q3_time']:
        if col in df.columns:
            df[f'{col}_ms'] = df[col].apply(convert_laptime_to_ms)
            q_cols_ms.append(f'{col}_ms')
    
    if q_cols_ms:
        df['bestQualiTime_ms'] = df[q_cols_ms].min(axis=1)
        if not df['bestQualiTime_ms'].isnull().all():
            pole_time_ms = df['bestQualiTime_ms'].min()
            df['GapToPole_ms'] = df['bestQualiTime_ms'] - pole_time_ms

    # --- 2. Features des Essais Libres ---
    fp_cols_ms = []
    for col in ['fp1_time', 'fp2_time', 'fp3_time']:
        if col in df.columns:
            df[f'{col}_ms'] = df[col].apply(convert_laptime_to_ms)
            fp_cols_ms.append(f'{col}_ms')

    if fp_cols_ms:
        df['FP_Best_LapTime_ms'] = df[fp_cols_ms].min(axis=1)
        df['FP_Best_LapTime_s'] = df['FP_Best_LapTime_ms'] / 1000.0
        df['FP_Rank'] = df['FP_Best_LapTime_ms'].rank(method='min')
        
    # --- 3. Features de Saison et d'Historique ---
    target_year = df['year'].iloc[0]
    target_round = df['round'].iloc[0]
    
    history_df = full_historical_df[
        (full_historical_df['year'] < target_year) |
        ((full_historical_df['year'] == target_year) & (full_historical_df['round'] < target_round))
    ].copy()
    
    history_df['position'] = pd.to_numeric(history_df['position'], errors='coerce')

    if not history_df.empty:
        driver_points = history_df.groupby('driver_code')['points'].sum()
        constructor_points = history_df.groupby('team')['points'].sum()
        dnf_counts = history_df[~history_df['time_or_retired'].str.contains(':', na=False)].groupby('driver_code').size()
        
        df['Driver_Championship_Points'] = df['driver_code'].map(driver_points).fillna(0)
        df['Constructor_Championship_Points'] = df['team'].map(constructor_points).fillna(0)
        df['Driver_DNF_Count_Season'] = df['driver_code'].map(dnf_counts).fillna(0)

        # NOUVELLE LOGIQUE POUR L'HISTORIQUE CIRCUIT
        current_race_name = df['race_name'].iloc[0]
        circuit_history_races = history_df[history_df['race_name'] == current_race_name]
        
        if circuit_history_races.empty:
            # Si aucune course passée sur ce circuit, on met 20 par défaut
            df['Driver_Circuit_History_AvgPos'] = 20
        else:
            # Sinon, on calcule la moyenne
            avg_pos_circuit = circuit_history_races.groupby('driver_code')['position'].mean()
            df['Driver_Circuit_History_AvgPos'] = df['driver_code'].map(avg_pos_circuit)

    # --- 4. Pondération de l'année ---
    min_year = full_historical_df['year'].min()
    max_year = full_historical_df['year'].max()
    if max_year > min_year:
        normalized_year = (df['year'] - min_year) / (max_year - min_year)
    else:
        normalized_year = 1.0
    df['year_weight'] = np.exp(normalized_year)

    # --- 5. Sélection des colonnes finales ---
    # On garde 'team' et 'race_name' pour le one-hot encoding, mais plus 'driver_code'
    features_to_keep = ['grid', 'team', 'race_name'] + base_feature_cols
    
    final_cols = [col for col in features_to_keep if col in df.columns]
    final_df = df[final_cols].copy()

    # Remplir les NaN restants
    for col in base_feature_cols:
         if col in final_df.columns and final_df[col].isnull().any():
            if col == 'Driver_Circuit_History_AvgPos':
                final_df[col] = final_df[col].fillna(20)
            else:
                final_df[col] = final_df[col].fillna(0)
            
    return final_df