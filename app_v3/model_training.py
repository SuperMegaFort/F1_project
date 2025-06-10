# model_training.py
import pandas as pd
import lightgbm as lgb
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import json
from config import *
from feature_engineering import create_features # Notre logique de features
from data_loader import load_and_prepare_historical_data # Notre nouveau chargeur

print("--- Lancement de l'Entraînement du Modèle Global ---")

# --- 1. Charger les données historiques déjà préparées ---
historical_df = load_and_prepare_historical_data()
if historical_df is None:
    exit() # Arrête le script si les données n'ont pas pu être chargées

# --- 2. Préparer le jeu de données d'entraînement ---
train_set_df = historical_df.copy() # On utilise toutes les données
print(f"Préparation des features pour {train_set_df['race_id'].nunique()} courses...")
feature_list, target_list = [], []

for race_id in train_set_df['race_id'].unique():
    race_weekend_data = historical_df[historical_df['race_id'] == race_id]
    features = create_features(historical_df, race_weekend_data)
    targets = race_weekend_data[['position']]
    if not features.empty and len(features) == len(targets):
        feature_list.append(features)
        target_list.append(targets)

if not feature_list:
    print("❌ ERREUR: Aucune feature n'a pu être générée.")
    exit()

X_train = pd.concat(feature_list, ignore_index=True)
y_train = pd.concat(target_list, ignore_index=True)

y_train['position'] = pd.to_numeric(y_train['position'], errors='coerce')
valid_indices = y_train.dropna().index
X_train = X_train.loc[valid_indices]
y_train = y_train.loc[valid_indices]

# --- 3. Définir et Entraîner le Pipeline ---
feature_columns = X_train.columns.tolist()
with open(FEATURE_COLUMNS_PATH, 'w') as f: json.dump(feature_columns, f)
print(f"Entraînement sur {len(X_train)} exemples.")

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', lgb.LGBMRegressor(objective='regression_l1', random_state=42))
])
pipeline.fit(X_train, y_train['position'])

# --- 4. Sauvegarder le modèle ---
joblib.dump(pipeline, MODEL_PATH)
print(f"✅ Modèle sauvegardé avec succès dans '{MODEL_PATH}'")
