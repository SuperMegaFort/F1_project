# utils.py
import streamlit as st
import pandas as pd
import os

# --- Global Variables & Constants ---
SESSION_FILES = {
    #"Course": "data/f1_2015-2024_race.csv",
    #"Qualifications": "data/f1_2015-2024_qualifying.csv",
    #"Essais Libres 1": "data/f1_2015-2024_practice_1.csv",
    #"Essais Libres 2": "data/f1_2015-2024_practice_2.csv",
    #"Essais Libres 3": "data/f1_2015-2024_practice_3.csv",
    #"Meilleur Tour en Course": "data/f1_2015-2024_fastest_lap.csv",
    #"Arrêts aux Stands": "data/f1_2015-2024_pit_stop.csv",
    #"Grille de Départ": "data/f1_2015-2024_starting_grid.csv"
    "Course": "data/race_all_years.csv",
    "Qualifications": "data/qualifying_all_years.csv",
    "Essais Libres 1": "data/practice_1_all_years.csv",
    "Essais Libres 2": "data/practice_2_all_years.csv",
    "Essais Libres 3": "data/practice_3_all_years.csv",
    "Meilleur Tour en Course": "data/fastest_lap_all_years.csv",
    "Arrêts aux Stands": "data/pit_stop_all_years.csv",
    "Grille de Départ": "data/starting_grid_all_years.csv"
}

YEAR_COLUMN = 'year'
GP_NAME_COLUMN = 'race_name'

# ========= A CHANGER QUAND LES DATASETS SERONT MIS A JOUR =========
VIS_DRIVER_COL = 'driver_name'
#VIS_DRIVER_COL= 'driver_number'
VIS_POSITION_COL = 'position'
POINTS_COL = 'points'
#POINTS_COL = 'time_or_retired'
#CONSTRUCTOR_COL = 'constructor_name'
CONSTRUCTOR_COL = 'team'
#CONSTRUCTOR_COL = 'driver_name'

# --- Data Loading Function ---
@st.cache_data
def load_data(file_path):
    """Loads data from a CSV file."""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if YEAR_COLUMN in df.columns:
                df[YEAR_COLUMN] = df[YEAR_COLUMN].astype(str)
            return df
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier {file_path}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def convert_df_to_csv(df):
    """Converts a DataFrame to CSV data."""
    return df.to_csv(index=False).encode('utf-8')

# Chemins vers les fichiers de données
HISTORICAL_DATA_PATH = 'data/F1_ALL_DATA_2020_2025.csv'
TEAMS_DATA_PATH = 'data/teams_summary.csv'

# Chemins pour le modèle (non utilisé dans cette page mais bon à avoir)
MODEL_PATH = 'f1_prediction_model.joblib'
FEATURE_COLUMNS_PATH = 'feature_columns.json'