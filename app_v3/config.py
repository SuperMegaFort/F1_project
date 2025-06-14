# config.py
import os
from pathlib import Path

# --- Configuration des Chemins ---

# Répertoire de base du projet (le dossier app_v3)
BASE_DIR = Path(__file__).resolve().parent

# --- Chemins des Données ---

# Dossier pour les données brutes et générées
DATA_DIR = BASE_DIR / "data_historical"
DATA_DIR.mkdir(exist_ok=True) # Crée le dossier s'il n'existe pas

# Données historiques d'entrée pour l'entraînement et l'application
HISTORICAL_DATA_PATH = DATA_DIR / "F1_ALL_DATA_2020_2024.csv"

# Données générées par les scripts de traitement
FEATURES_DATA_PATH = DATA_DIR / "F1_FEATURES_ENCODED.csv"
TEAMS_DATA_PATH = DATA_DIR / "teams_summary_data.csv"


# --- Chemins du Modèle ---

# Dossier pour les modèles entraînés et les métadonnées
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)

# Fichiers du modèle
MODEL_PATH = MODEL_DIR / "f1_lgbm_model.joblib"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"
