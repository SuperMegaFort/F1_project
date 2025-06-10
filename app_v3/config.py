# config.py
from pathlib import Path

# --- Configuration des Chemins ---
BASE_DIR = Path(__file__).resolve().parent

# Chemin vers les données historiques pour l'entraînement (un seul fichier)
HISTORICAL_DATA_PATH = BASE_DIR / "data_historical" / "F1_ALL_DATA_2020_2024.csv"

# Chemin vers les nouvelles données pour la prédiction (un seul fichier)
NEW_DATA_PATH = BASE_DIR / "data_new" / "F1_ALL_DATA_2025.csv"

# Dossier pour les modèles entraînés et les métadonnées
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True) # Crée le dossier s'il n'existe pas$

ALL_DATA_PATH = BASE_DIR / "data_all" / "F1_ALL_DATA_2020_2025.csv"

# Modèle et métadonnées
MODEL_PATH = MODELS_DIR / "ranking_regressor.joblib"
FEATURE_COLUMNS_PATH = MODELS_DIR / "feature_columns.json"

# config.py
from pathlib import Path

# --- Configuration des Chemins ---
BASE_DIR = Path(__file__).resolve().parent

# Chemin vers votre grand fichier de données contenant TOUT (2020-2025)
# Assurez-vous que ce fichier se trouve bien dans un dossier 'data_all'

