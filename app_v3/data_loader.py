# data_loader.py
import pandas as pd
from config import HISTORICAL_DATA_PATH, NEW_DATA_PATH

def load_and_prepare_historical_data():
    """
    Charge le grand fichier de données historiques et s'assure que toutes les 
    colonnes nécessaires, comme 'round', sont présentes et correctement formatées.
    C'est la source de vérité unique pour les données historiques.
    """
    print("Chargement et préparation des données historiques...")
    try:
        df = pd.read_csv(HISTORICAL_DATA_PATH)
    except FileNotFoundError:
        print(f"ERREUR: Fichier historique introuvable: {HISTORICAL_DATA_PATH}")
        return None

    # On vérifie et génère la colonne 'round' si elle est manquante
    if 'round' not in df.columns:
        print("Génération de la colonne 'round' manquante...")
        df['race_id'] = pd.to_numeric(df['race_id'], errors='coerce').dropna().astype(int)
        
        # On crée une table de correspondance (race_id -> round) pour chaque année
        rounds_map = df[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
        rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
        
        # On fusionne cette nouvelle colonne 'round' dans notre DataFrame principal
        df = pd.merge(df, rounds_map[['race_id', 'round']], on='race_id', how='left')
    
    print("Données historiques prêtes.")
    return df

def load_new_data():
    """Charge les données de la nouvelle saison (ex: 2025)."""
    try:
        df = pd.read_csv(NEW_DATA_PATH)
        # On fait la même chose pour les données de 2025
        if 'round' not in df.columns:
            df['race_id'] = pd.to_numeric(df['race_id'], errors='coerce').dropna().astype(int)
            rounds_map = df[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
            rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
            df = pd.merge(df, rounds_map[['race_id', 'round']], on='race_id', how='left')
        return df
    except FileNotFoundError:
        print(f"ERREUR: Fichier de nouvelles données introuvable: {NEW_DATA_PATH}")
        return None
