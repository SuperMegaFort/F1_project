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
    print(f"Chargement du fichier de données historiques : {HISTORICAL_DATA_PATH}")
    historical_df = pd.read_csv(HISTORICAL_DATA_PATH)
except FileNotFoundError:
    print(f"❌ ERREUR: Le fichier '{HISTORICAL_DATA_PATH}' est introuvable.")
    exit()

# --- 2. Générer la colonne 'round' si manquante ---
if 'round' not in historical_df.columns:
    print("Génération de la colonne 'round' manquante...")
    historical_df['race_id'] = pd.to_numeric(historical_df['race_id'], errors='coerce')
    historical_df.dropna(subset=['race_id'], inplace=True)
    historical_df['race_id'] = historical_df['race_id'].astype(int)
    rounds_map = historical_df[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
    rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
    historical_df = pd.merge(historical_df, rounds_map[['race_id', 'round']], on='race_id', how='left')

# --- 3. Préparer le jeu de données d'entraînement ---
print(f"Préparation des features pour {historical_df['race_id'].nunique()} courses...")
feature_list, target_list = [], []

for race_id in historical_df['race_id'].unique():
    race_weekend_data = historical_df[historical_df['race_id'] == race_id].copy()
    features = create_features(historical_df, race_weekend_data)
    targets = race_weekend_data[['position']].copy()
    
    # Garder des identifiants pour la jointure
    features['race_id'] = race_id
    # Il nous faut un identifiant unique par ligne, driver_number + race_id est bon
    features['temp_id'] = race_weekend_data['driver_number'].astype(str) + "_" + race_weekend_data['race_id'].astype(str)
    targets['temp_id'] = race_weekend_data['driver_number'].astype(str) + "_" + race_weekend_data['race_id'].astype(str)


    feature_list.append(features)
    target_list.append(targets)

if not feature_list:
    print("❌ ERREUR: Aucune feature n'a pu être générée.")
    exit()

X_train_raw = pd.concat(feature_list, ignore_index=True)
y_train_raw = pd.concat(target_list, ignore_index=True)

# --- 4. Appliquer le One-Hot Encoding ---
print("Application du One-Hot Encoding...")
categorical_features = ['team', 'race_name']
X_train_encoded = pd.get_dummies(X_train_raw, columns=categorical_features, prefix=categorical_features)

# Fusionner pour aligner features et cibles
merged_df = pd.merge(X_train_encoded, y_train_raw.drop_duplicates(subset=['temp_id']), on='temp_id')

merged_df['position'] = pd.to_numeric(merged_df['position'], errors='coerce')
merged_df.dropna(subset=['position'], inplace=True)

y_train = merged_df[['position']]
X_train = merged_df.drop(columns=['position', 'race_id', 'temp_id'])

# --- 5. Sauvegarder le DataFrame de features ---
try:
    print(f"Sauvegarde du fichier de features encodées dans : {FEATURES_DATA_PATH}")
    # Ajout de la cible pour l'analyse post-entraînement
    X_train_to_save = X_train.copy()
    X_train_to_save['TARGET_position'] = y_train['position'].values
    X_train_to_save.to_csv(FEATURES_DATA_PATH, index=False)
    print("✅ Fichier de features sauvegardé avec succès.")
except Exception as e:
    print(f"❌ ERREUR lors de la sauvegarde du fichier CSV : {e}")

# --- 6. Définir et Entraîner le Pipeline ---
feature_columns = X_train.columns.tolist()
with open(FEATURE_COLUMNS_PATH, 'w') as f:
    json.dump(feature_columns, f)

print(f"Entraînement sur {len(X_train)} exemples avec {len(feature_columns)} features.")

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', lgb.LGBMRegressor(objective='regression_l1', random_state=42))
])
pipeline.fit(X_train, y_train['position'])

# --- 7. Sauvegarder le modèle entraîné ---
joblib.dump(pipeline, MODEL_PATH)
print(f"✅ Modèle sauvegardé avec succès dans '{MODEL_PATH}'")