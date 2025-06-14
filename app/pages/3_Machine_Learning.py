# pages/3_Machine_Learning.py
import streamlit as st
import pandas as pd
import os
import joblib
import json
from feature_engineering import create_features 

# Import shared functions and constants from utils.py
from utils import (
    load_data,
    YEAR_COLUMN,
    GP_NAME_COLUMN,
    VIS_DRIVER_COL,
    CONSTRUCTOR_COL,
    VIS_POSITION_COL
)

st.set_page_config(
    layout="wide",
    page_title="Machine Learning F1",
    page_icon="🤖"
)

st.title("🤖 Prédictions de Course par Machine Learning")
st.markdown("""
Cette section utilise un modèle de Machine Learning pour prédire les résultats des courses de Formule 1.
""")
st.markdown("---")

TEAM_AESTHETICS = {
    'Mercedes': {'color': '#6CD3BF', 'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Mercedes-Benz_Star.svg/1200px-Mercedes-Benz_Star.svg.png'},
    'Ferrari': {'color': '#F91536', 'logo': 'https://upload.wikimedia.org/wikipedia/fr/thumb/c/c0/Scuderia_Ferrari_Logo.svg/1517px-Scuderia_Ferrari_Logo.svg.png'},
    'Red Bull Racing Honda RBPT': {'color': '#3671C6', 'logo': 'https://brandlogo.org/wp-content/uploads/2024/09/Red-Bull-Logo-1987.png.webp'},
    'McLaren Mercedes': {'color': '#F58020', 'logo': 'https://r.testifier.nl/Acbs8526SDKI/resizing_type:fill/plain/https%3A%2F%2Fs3-newsifier.ams3.digitaloceanspaces.com%2Fgpblog.com%2Fimages%2F2025-03%2Fmclaren-logo-67e9539536b57.png'},
    'Aston Martin Aramco Mercedes': {'color': '#358C75', 'logo': 'https://www.pngplay.com/wp-content/uploads/13/Aston-Martin-Logo-No-Background.png'},
    'Alpine Renault': {'color': '#2293D1', 'logo': 'https://logodownload.org/wp-content/uploads/2022/03/alpine-f1-logo-0.png'},
    'Williams Mercedes': {'color': '#64C4FF', 'logo': 'https://brandlogo.org/wp-content/uploads/2025/02/Williams-Racing-Icon-2020.png.webp'},
    'Racing Bulls Honda RBPT': {'color': '#6692FF', 'logo': 'https://static.wikia.nocookie.net/rr3/images/e/ef/F1.Racing.Bulls.png'},
    'Kick Sauber Ferrari': {'color': '#52E252', 'logo': 'https://fansbrands.de/cdn/shop/collections/kick-logo-500x500-collection.png?crop=center&height=1200&v=1728150625&width=1200'},
    'Haas Ferrari': {'color': "#FFFFFF", 'logo': 'https://upload.wikimedia.org/wikipedia/commons/d/d4/Logo_Haas_F1.png'},    
    'Default': {'color': '#333333', 'logo': ''}
}

SHARED_DRIVER_CARD_STYLES = """
<style>
    .driver-card {
        display: flex;
        align-items: center;
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 5px;
        margin-bottom: 5px; /* Espace entre les cartes */
        height: 55px;
    }
    .position {
        font-size: 24px;
        font-weight: bold;
        color: #ffffff;
        width: 80px;
        text-align: center;
        flex-shrink: 0;
    }
    .driver-info {
        flex-grow: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 100%;
        padding-left: 15px;
        border-radius: 5px;
        position: relative;
        overflow: hidden;
    }
    .driver-name {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        text-shadow: 1px 1px 2px #000;
        z-index: 2;
    }
    .team-logo {
        height: 150%;
        width: auto;
        position: absolute;
        right: 10%;
        top: 50%;
        transform: translateY(-50%);
        z-index: 1;
    }
</style>
"""

def get_ordinal(n):
    if pd.isna(n):
        return "DNF"
    n = int(n)
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix.upper()

def display_predicted_grid(results_df):   
    st.subheader("🤖 Grille de Résultats Prédits")
    
    col1, col2 = st.columns(2, gap="medium")
    
    odd_drivers = results_df.iloc[::2]
    even_drivers = results_df.iloc[1::2]

    with col1:
        for _, row in odd_drivers.iterrows():
            team_style = TEAM_AESTHETICS.get(row[CONSTRUCTOR_COL], TEAM_AESTHETICS['Default'])
            html = f"""
            <div class="driver-card">
                <div class="position">{get_ordinal(row['predicted_rank'])}</div>
                <div class="driver-info" style="background-color: {team_style['color']};">
                    <span class="driver-name">{row[VIS_DRIVER_COL]}</span>
                    <img src="{team_style['logo']}" class="team-logo">
                </div>
            </div>"""
            st.markdown(html, unsafe_allow_html=True)
            
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        for _, row in even_drivers.iterrows():
            team_style = TEAM_AESTHETICS.get(row[CONSTRUCTOR_COL], TEAM_AESTHETICS['Default'])
            html = f"""
            <div class="driver-card">
                <div class="position">{get_ordinal(row['predicted_rank'])}</div>
                <div class="driver-info" style="background-color: {team_style['color']};">
                    <span class="driver-name">{row[VIS_DRIVER_COL]}</span>
                    <img src="{team_style['logo']}" class="team-logo">
                </div>
            </div>"""
            st.markdown(html, unsafe_allow_html=True)

def display_actual_grid(results_df):
    st.subheader("🏆 Grille des Résultats Réels")
    
    temp_df = results_df.copy()
    temp_df['numeric_pos'] = pd.to_numeric(temp_df[VIS_POSITION_COL], errors='coerce')

    finishers = temp_df[temp_df['numeric_pos'].notna()].sort_values(by='numeric_pos')
    non_finishers = temp_df[temp_df['numeric_pos'].isna()]

    actual_sorted_df = pd.concat([finishers, non_finishers])

    col1, col2 = st.columns(2, gap="medium")
    
    odd_drivers = actual_sorted_df.iloc[::2]
    even_drivers = actual_sorted_df.iloc[1::2]

    with col1:
        for _, row in odd_drivers.iterrows():
            team_style = TEAM_AESTHETICS.get(row[CONSTRUCTOR_COL], TEAM_AESTHETICS['Default'])
            html = f"""
            <div class="driver-card">
                <div class="position">{get_ordinal(row[VIS_POSITION_COL])}</div>
                <div class="driver-info" style="background-color: {team_style['color']};">
                    <span class="driver-name">{row[VIS_DRIVER_COL]}</span>
                    <img src="{team_style['logo']}" class="team-logo">
                </div>
            </div>"""
            st.markdown(html, unsafe_allow_html=True)
            
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        for _, row in even_drivers.iterrows():
            team_style = TEAM_AESTHETICS.get(row[CONSTRUCTOR_COL], TEAM_AESTHETICS['Default'])
            html = f"""
            <div class="driver-card">
                <div class="position">{get_ordinal(row[VIS_POSITION_COL])}</div>
                <div class="driver-info" style="background-color: {team_style['color']};">
                    <span class="driver-name">{row[VIS_DRIVER_COL]}</span>
                    <img src="{team_style['logo']}" class="team-logo">
                </div>
            </div>"""
            st.markdown(html, unsafe_allow_html=True)

# --- Define paths & Load Model ---
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "f1_lgbm_model.joblib")
FEATURES_PATH = os.path.join(MODEL_DIR, "feature_columns.json")
ML_DATA_PATH = "data/F1_ALL_DATA_2020_2025.csv"

@st.cache_resource(ttl="6h")
def load_model_and_features():
    if not os.path.exists(FEATURES_PATH):
        return None, None, f"Fichier de caractéristiques introuvable : `{FEATURES_PATH}`"
    try:
        with open(FEATURES_PATH, 'r') as f:
            features = json.load(f)
    except Exception as e:
        return None, None, f"Erreur de lecture de `{FEATURES_PATH}`: {e}"

    if not os.path.exists(MODEL_PATH):
        return None, None, f"Fichier de modèle introuvable : `{MODEL_PATH}`. Veuillez d'abord entraîner un modèle."
    try:
        model = joblib.load(MODEL_PATH)
        st.success("Modèle pré-entraîné et caractéristiques chargés avec succès !")
        return model, features, None
    except Exception as e:
        return None, None, f"Erreur de chargement du modèle `{MODEL_PATH}`: {e}"

# --- Data Loading ---
df_full_dataset = pd.DataFrame()
if os.path.exists(ML_DATA_PATH):
    df_full_dataset = load_data(ML_DATA_PATH)
    for col in ['grid', 'position', 'year', 'race_id', 'driver_number', 'circuitId']:
        if col in df_full_dataset.columns:
            df_full_dataset[col] = pd.to_numeric(df_full_dataset[col], errors='coerce')
    if 'round' not in df_full_dataset.columns and 'race_id' in df_full_dataset.columns:        
        df_full_dataset.dropna(subset=['year', 'race_id'], inplace=True)
        df_full_dataset['race_id'] = df_full_dataset['race_id'].astype(int)
        rounds_map = df_full_dataset[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
        rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
        df_full_dataset = pd.merge(df_full_dataset, rounds_map[['race_id', 'round']], on='race_id', how='left')
        df_full_dataset['round'] = pd.to_numeric(df_full_dataset['round'], errors='coerce')


# --- Main Logic ---
if df_full_dataset.empty:
    st.error(f"Fichier de données pour le ML ({ML_DATA_PATH}) introuvable ou vide.")
else:
    model, features, error_msg = load_model_and_features()

    if error_msg:
        st.error(error_msg)
    elif model and features:
        st.header("🔮 Faire une Prédiction")
        
        col1, col2 = st.columns(2)
        all_years = sorted(df_full_dataset[YEAR_COLUMN].dropna().unique().astype(int), reverse=True)
        
        with col1:
            selected_year_ml = st.selectbox("1. Choisissez une année", all_years, key="ml_year_select")
        with col2:
            races_in_year = sorted(df_full_dataset[df_full_dataset[YEAR_COLUMN] == selected_year_ml][GP_NAME_COLUMN].unique())
            selected_race_ml = st.selectbox("2. Choisissez un Grand Prix", races_in_year, key="ml_race_select")

        if st.button("🚀 Prédire le Classement", use_container_width=True):
            with st.spinner("Création des caractéristiques et prédiction en cours..."):
                race_weekend_data = df_full_dataset[
                    (df_full_dataset[YEAR_COLUMN] == selected_year_ml) &
                    (df_full_dataset[GP_NAME_COLUMN] == selected_race_ml)
                ].copy()

                if race_weekend_data.empty:
                    st.warning("Aucune donnée de base trouvée pour cette course.")
                else:
                    features_df = create_features(df_full_dataset, race_weekend_data)

                    if features_df.empty:
                        st.error("Impossible de générer les caractéristiques pour la prédiction.")
                    else:
                        missing_cols = set(features) - set(features_df.columns)
                        for c in missing_cols:
                            features_df[c] = 0
                        
                        X_pred = features_df[features]
                        predicted_values = model.predict(X_pred)
                        result_df = race_weekend_data.copy()
                        result_df['predicted_value'] = predicted_values
                        result_df = result_df.sort_values(by='predicted_value').reset_index(drop=True)
                        result_df['predicted_rank'] = result_df.index + 1

                        st.markdown("---")
                        
                        st.markdown(SHARED_DRIVER_CARD_STYLES, unsafe_allow_html=True)
                        
                        col_pred, col_actual = st.columns(2, gap="medium")
                        # 1. Afficher la grille des résultats prédits                            
                        with col_pred:
                            with st.container(border=True):
                                display_predicted_grid(result_df)
                                st.markdown("<br>", unsafe_allow_html=True)
                        with col_actual:
                            with st.container(border=True):
                                has_actual_results = VIS_POSITION_COL in result_df.columns and result_df[VIS_POSITION_COL].notna().any()
                                if has_actual_results:
                                    display_actual_grid(result_df)
                                else:
                                    st.info("Les résultats réels ne sont pas encore disponibles pour cette course.")
                                st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("---")

                        # 3. Afficher le DataFrame de comparaison et le MAE
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.subheader("🔮 Tableau des Résultats")
                        display_cols = [VIS_DRIVER_COL, CONSTRUCTOR_COL, 'predicted_rank', VIS_POSITION_COL]
                        display_cols_exist = [c for c in display_cols if c in result_df.columns]
                        st.dataframe(
                            result_df[display_cols_exist].rename(columns={
                                'predicted_rank': 'Rang Prédit',
                                VIS_DRIVER_COL: 'Pilote',
                                CONSTRUCTOR_COL: 'Écurie',
                                VIS_POSITION_COL: 'Position Réelle'
                            }),
                            use_container_width=True
                        )
                        
                        if has_actual_results:
                            mae_df = result_df.dropna(subset=[VIS_POSITION_COL])
                            mae = (mae_df['predicted_rank'] - pd.to_numeric(mae_df[VIS_POSITION_COL])).abs().mean()
                            st.metric(
                                label="Erreur Absolue Moyenne (MAE)", 
                                value=f"{mae:.2f}",
                                help="La différence moyenne entre le rang prédit et le rang réel."
                            )