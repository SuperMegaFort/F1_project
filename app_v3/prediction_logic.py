# prediction_logic.py
import pandas as pd
import joblib
import json
from config import *
from feature_engineering import create_features 

def run_prediction(model, training_feature_columns, full_dataset, year, race_name):
    """
    Orchestre tout le processus de prédiction pour une course donnée.
    """
    try:
        # 1. Isoler les données du week-end pour la prédiction
        race_weekend_data = full_dataset[
            (full_dataset['year'] == year) & 
            (full_dataset['race_name'] == race_name)
        ].copy()

        if race_weekend_data.empty:
            return f"Course '{race_name} {year}' non trouvée dans le jeu de données."

        actual_positions = race_weekend_data[['driver_code', 'team', 'grid', 'position']].copy()
        
        # 2. Créer les features
        features_df_raw = create_features(full_dataset, race_weekend_data)
        if features_df_raw.empty: return "Impossible de générer les features."
        
        # 3. Appliquer le One-Hot Encoding
        # CORRECTION : On ne one-hot encode plus 'driver_code'
        categorical_features = ['team', 'race_name']
        features_df_encoded = pd.get_dummies(features_df_raw, columns=categorical_features, prefix=categorical_features)
        
        # 4. Aligner le DataFrame sur les colonnes du modèle
        features_df_aligned = features_df_encoded.reindex(columns=training_feature_columns, fill_value=0)
        
        # 5. Prédire
        predictions = model.predict(features_df_aligned)
        
        # 6. Préparer le tableau de résultats
        result_df = actual_positions.rename(columns={'position': 'ActualPosition'})
        # Assurer que l'index de result_df correspond à celui de features_df_aligned pour l'assignation
        result_df = result_df.set_index(features_df_aligned.index)
        result_df['PredictedPositionValue'] = predictions
        result_df = result_df.sort_values(by='PredictedPositionValue').reset_index(drop=True)
        result_df['PredictedRank'] = result_df.index + 1
        
        return result_df

    except FileNotFoundError:
        return "ERREUR CRITIQUE : Fichier de modèle (.joblib) ou de colonnes (.json) non trouvé. Veuillez exécuter 'model_training.py' d'abord."
    except Exception as e:
        import traceback
        return f"Erreur inattendue : {e}\n{traceback.format_exc()}"