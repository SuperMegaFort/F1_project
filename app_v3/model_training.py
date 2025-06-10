# model_training.py
import pandas as pd
import lightgbm as lgb
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import json
from config import *
from feature_engineering import create_features 

print("--- Lancement de l'Entraînement du Modèle Global ---")

# --- 1. Charger le dataset historique unique ---
try:
    historical_df = pd.read_csv(HISTORICAL_DATA_PATH)
except FileNotFoundError:
    print(f"❌ ERREUR: Le fichier '{HISTORICAL_DATA_PATH}' est introuvable.")
    print("Veuillez vous assurer que votre fichier F1_ALL_DATA_2020_2024.csv est bien dans le dossier 'data_historical/'.")
    exit()

# --- 2. Générer la colonne 'round' si elle est manquante ---
if 'round' not in historical_df.columns:
    print("Génération de la colonne 'round' manquante...")
    historical_df['race_id'] = pd.to_numeric(historical_df['race_id'], errors='coerce').dropna().astype(int)
    rounds_map = historical_df[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
    rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
    historical_df = pd.merge(historical_df, rounds_map[['race_id', 'round']], on='race_id', how='left')

# --- 3. Préparer le jeu de données d'entraînement ---
train_set_df = historical_df.copy() # On utilise toutes les données 2020-2024
print(f"Préparation des features pour {train_set_df['race_id'].nunique()} courses...")
feature_list, target_list = [], []

for race_id in train_set_df['race_id'].unique():
    race_weekend_data = historical_df[historical_df['race_id'] == race_id]
    features = create_features(historical_df, race_weekend_data)
    
    # --- CORRECTION 1: Utiliser la bonne colonne 'position' comme cible ---
    targets = race_weekend_data[['position']] 
    
    if not features.empty and len(features) == len(targets):
        feature_list.append(features)
        target_list.append(targets)

if not feature_list:
    print("❌ ERREUR: Aucune feature n'a pu être générée.")
    exit()

X_train = pd.concat(feature_list, ignore_index=True)
y_train = pd.concat(target_list, ignore_index=True)

# --- CORRECTION 2: Nettoyer la colonne cible ---
# Convertir la position en numérique. Les valeurs comme 'NC' deviendront NaN (Not a Number).
y_train['position'] = pd.to_numeric(y_train['position'], errors='coerce')

# Garder uniquement les lignes où nous avons une position finale valide (pas de DNF/NC)
# C'est essentiel pour que le modèle apprenne à prédire un rang de fin de course.
valid_indices = y_train.dropna(subset=['position']).index

# Filtrer X_train et y_train pour qu'ils correspondent et ne contiennent pas de NaN
X_train = X_train.loc[valid_indices]
y_train = y_train.loc[valid_indices]

# --- 4. Définir et Entraîner le Pipeline ---
feature_columns = X_train.columns.tolist()
with open(FEATURE_COLUMNS_PATH, 'w') as f:
    json.dump(feature_columns, f)

print(f"Entraînement sur {len(X_train)} exemples (uniquement les pilotes ayant terminé la course).")

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', lgb.LGBMRegressor(objective='regression_l1', random_state=42))
])

# Entraîner sur la colonne 'position' nettoyée
pipeline.fit(X_train, y_train['position'])

# --- 5. Sauvegarder le modèle ---
joblib.dump(pipeline, MODEL_PATH)
print(f"✅ Modèle sauvegardé avec succès dans '{MODEL_PATH}'")
