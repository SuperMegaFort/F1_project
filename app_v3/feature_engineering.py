# feature_engineering.py
import pandas as pd
import numpy as np

def create_features(full_historical_df, race_weekend_data):
    """
    Crée le jeu de features pour une course en combinant données historiques et du week-end.
    Version corrigée pour gérer les cas sans historique.
    """
    # Correction pour le SettingWithCopyWarning: on travaille sur une copie explicite
    df = race_weekend_data.copy()
    
    # --- Initialisation de toutes les colonnes de features ---
    # Cela garantit qu'elles existeront toujours, même si elles ne peuvent pas être calculées.
    feature_cols = [
        'GapToPole_ms', 'FP_Best_LapTime_ms', 'FP_Rank',
        'Driver_Championship_Points', 'Constructor_Championship_Points',
        'Driver_DNF_Count_Season', 'Driver_Circuit_History_AvgPos'
    ]
    for col in feature_cols:
        df[col] = np.nan # On les initialise avec une valeur "Not a Number"

    # --- 1. Features de Qualification ---
    time_cols = [col for col in ['q1_time', 'q2_time', 'q3_time'] if col in df.columns]
    for col in time_cols: df[col] = pd.to_timedelta(df[col], errors='coerce')
    if time_cols:
        df['bestQualiTime'] = df[time_cols].min(axis=1)
        if not df['bestQualiTime'].isnull().all():
            pole_time = df['bestQualiTime'].min()
            df['GapToPole_ms'] = (df['bestQualiTime'] - pole_time).dt.total_seconds() * 1000

    # --- 2. Features des Essais Libres ---
    fp_cols = [col for col in ['fp1_time', 'fp2_time', 'fp3_time'] if col in df.columns]
    for col in fp_cols: df[col] = pd.to_timedelta(df[col], errors='coerce')
    if fp_cols:
        df['FP_Best_LapTime'] = df[fp_cols].min(axis=1)
        df['FP_Best_LapTime_ms'] = df['FP_Best_LapTime'].dt.total_seconds() * 1000
        df['FP_Rank'] = df['FP_Best_LapTime_ms'].rank(method='min')

    # --- 3. Features de Saison et d'Historique ---
    target_year = df['year'].iloc[0]
    target_round = df['round'].iloc[0] 
    
    history_df = full_historical_df[
        (full_historical_df['year'] < target_year) |
        ((full_historical_df['year'] == target_year) & (full_historical_df['round'] < target_round))
    ]

    if not history_df.empty:
        driver_points = history_df.groupby('driver_number')['points'].sum()
        constructor_points = history_df.groupby('team')['points'].sum()
        dnf_counts = history_df[~history_df['time_or_retired'].str.contains(':', na=False)].groupby('driver_number').size()

        df['Driver_Championship_Points'] = df['driver_number'].map(driver_points).fillna(0)
        df['Constructor_Championship_Points'] = df['team'].map(constructor_points).fillna(0)
        df['Driver_DNF_Count_Season'] = df['driver_number'].map(dnf_counts).fillna(0)
        
        # Le calcul de l'historique sur circuit ne se fait que si la colonne existe
        if 'circuitId' in df.columns and 'circuitId' in history_df.columns:
            circuit_id = df['circuitId'].iloc[0]
            circuit_history = history_df[history_df['circuitId'] == circuit_id]
            avg_pos_circuit = circuit_history.groupby('driver_number')['position'].mean()
            df['Driver_Circuit_History_AvgPos'] = df['driver_number'].map(avg_pos_circuit)

    # --- Nettoyage et sélection des colonnes finales ---
    features_to_keep = ['grid'] + feature_cols
    
    final_df = df[features_to_keep].copy()

    # Remplir les NaN restants (par exemple, pour la première course) avec 0 ou la médiane
    for col in final_df.columns:
        if final_df[col].isnull().any():
            final_df[col] = final_df[col].fillna(0)
    
    return final_df
