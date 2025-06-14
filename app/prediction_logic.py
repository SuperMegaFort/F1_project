# prediction_logic.py
import pandas as pd
import joblib
import json
from config import *
from feature_engineering import create_features # On réutilise notre logique de features

def run_prediction(full_dataset, year, race_name):
    """
    Orchestre tout le processus de prédiction pour une course donnée.
    
    Args:
        full_dataset (pd.DataFrame): Le DataFrame complet contenant toutes les données.
        year (int): L'année de la course à prédire.
        race_name (str): Le nom de la course à prédire.
    """
    try:
        # 1. Charger le modèle et les colonnes de features
        model = joblib.load(MODEL_PATH)
        with open(FEATURE_COLUMNS_PATH) as f:
            feature_columns = json.load(f)
        
        # 2. Isoler les données du week-end pour la prédiction
        race_weekend_data = full_dataset[
            (full_dataset['year'] == year) & 
            (full_dataset['race_name'] == race_name)
        ]
        if race_weekend_data.empty:
            return f"Course '{race_name} {year}' non trouvée dans le jeu de données."

        # 3. Créer les features
        # On passe le dataset complet pour qu'il puisse calculer l'historique
        features_df = create_features(full_dataset, race_weekend_data)
        if features_df.empty: return "Impossible de générer les features."
        
        # S'assurer que les colonnes sont dans le bon ordre pour le modèle
        features_df = features_df[feature_columns]
        
        # 4. Prédire
        predictions = model.predict(features_df)
        
        # 5. Préparer le tableau de résultats
        result_df = race_weekend_data[['driver_code', 'team', 'grid', 'position']].copy()
        result_df.rename(columns={'position': 'ActualPosition'}, inplace=True)
        result_df['PredictedPositionValue'] = predictions
        result_df = result_df.sort_values(by='PredictedPositionValue').reset_index(drop=True)
        result_df['PredictedRank'] = result_df.index + 1
        
        return result_df

    except FileNotFoundError:
        return "ERREUR CRITIQUE : Fichier de modèle (.joblib) ou de colonnes (.json) non trouvé. Veuillez exécuter 'model_training.py' d'abord."
    except Exception as e:
        import traceback
        return f"Erreur inattendue : {e}\n{traceback.format_exc()}"
