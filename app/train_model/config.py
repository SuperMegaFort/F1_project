import os
from pathlib import Path

# --- Configuration des Chemins ---

# Répertoire de base du projet (le dossier app_v3)

# --- Chemins des Données ---

# Dossier pour les données brutes et générées
# Utiliser Path pour que l'opérateur / fonctionne
DATA_DIR = Path("data") 
DATA_DIR.mkdir(exist_ok=True) # Crée le dossier s'il n'existe pas

# Données historiques d'entrée pour l'entraînement et l'application
HISTORICAL_DATA_PATH = DATA_DIR / "F1_ALL_DATA_2020_2024.csv"

# Données générées par les scripts de traitement
FEATURES_DATA_PATH = DATA_DIR / "F1_FEATURES_ENCODED.csv"
TEAMS_DATA_PATH = DATA_DIR / "teams_summary_data.csv"


# --- Chemins du Modèle ---

# Dossier pour les modèles entraînés et les métadonnées
# Utiliser Path pour le dossier du modèle également
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

# Fichiers du modèle
MODEL_PATH = MODEL_DIR / "f1_lgbm_model.joblib"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"
