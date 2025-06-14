# app.py
import streamlit as st
import pandas as pd
import joblib
import json
import altair as alt
from config import *
from prediction_logic import run_prediction

# --- Configuration de la Page et du Style ---
st.set_page_config(page_title="F1 Vision", layout="wide", initial_sidebar_state="expanded")

# Injection de CSS (inchangé)
st.markdown("""
<style>
    /* ... (votre CSS existant) ... */
</style>
""", unsafe_allow_html=True)


# --- Fonctions de chargement des données (avec cache) ---
@st.cache_data(ttl="6h")
def load_main_dataset():
    """Charge le grand fichier de données F1 et le prépare."""
    try:
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        if 'round' not in df.columns:
            df['race_id'] = pd.to_numeric(df['race_id'], errors='coerce').dropna().astype(int)
            rounds_map = df[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
            rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
            df = pd.merge(df, rounds_map[['race_id', 'round']], on='race_id', how='left')
        return df
    except FileNotFoundError:
        st.error(f"Dataset principal introuvable ! Assurez-vous que '{HISTORICAL_DATA_PATH}' existe.")
        return None

@st.cache_data(ttl="6h")
def load_teams_data():
    """Charge le fichier récapitulatif des écuries."""
    try:
        df = pd.read_csv(TEAMS_DATA_PATH)
        return df
    except FileNotFoundError:
        st.error(f"Fichier de données des écuries introuvable ! Exécutez `data_processing_teams.py`.")
        return None
        
@st.cache_resource
def load_model_and_columns():
    """Charge le modèle et la liste des colonnes de features."""
    try:
        model = joblib.load(MODEL_PATH)
        with open(FEATURE_COLUMNS_PATH, 'r') as f:
            feature_columns = json.load(f)
        return model, feature_columns
    except FileNotFoundError:
        st.error(f"Modèle '{MODEL_PATH}' ou fichier de colonnes introuvable. Avez-vous exécuté model_training.py ?")
        return None, None

# --- Application Principale ---
st.markdown("<h1 style='text-align: center; font-weight: bold;'>F1 VISION DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("---")

# Charger toutes les données au démarrage
full_data = load_main_dataset()
teams_summary = load_teams_data()
model, feature_columns = load_model_and_columns()

if full_data is not None:
    # --- Barre Latérale (Sidebar) ---
    with st.sidebar:
        st.image("https://www.formula1.com/etc/designs/fom-website/images/f1_logo.svg", width=100)
        st.header("Filtres")
        # MISE À JOUR : Permettre la sélection de toutes les années, y compris 2025
        display_years = sorted(full_data['year'].unique(), reverse=True)
        selected_year = st.selectbox("Choisissez une année :", options=display_years)

    season_data = full_data[full_data['year'] == selected_year].copy()

    # --- Définition des Onglets ---
    tabs = st.tabs([
        "🏆 Pilotes", 
        "🛠️ Constructeurs", 
        "🏎️ Écuries Détails",
        "📈 Progression", 
        "🎯 Prédictions"
    ])
    
    # Onglet 1 : Classement Pilotes
    with tabs[0]:
        st.header(f"🏆 Classement Final des Pilotes - {selected_year}")
        if not season_data.empty:
            driver_standings = season_data.groupby(['driver_code', 'team'])['points'].sum().reset_index()
            driver_standings = driver_standings.sort_values(by='points', ascending=False).reset_index(drop=True)
            driver_standings['Position'] = driver_standings.index + 1
            st.dataframe(driver_standings[['Position', 'driver_code', 'team', 'points']], use_container_width=True)
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")

    # Onglet 2 : Classement Constructeurs
    with tabs[1]:
        st.header(f"🛠️ Classement Final des Constructeurs - {selected_year}")
        if not season_data.empty:
            constructor_standings = season_data.groupby('team')['points'].sum().reset_index()
            constructor_standings = constructor_standings.sort_values(by='points', ascending=False).reset_index(drop=True)
            constructor_standings['Position'] = constructor_standings.index + 1
            st.dataframe(constructor_standings[['Position', 'team', 'points']], use_container_width=True)
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")
        
    # Onglet 3 : Écuries Détails
    with tabs[2]:
        st.header(f"🏎️ Détails des Écuries - {selected_year}")
        if teams_summary is not None:
            # MISE À JOUR : On filtre maintenant les données des écuries avec l'année sélectionnée
            year_teams_data = teams_summary[teams_summary['Year'] == selected_year]
            if not year_teams_data.empty:
                sorted_teams = year_teams_data[['TeamName', 'TeamPoints']].drop_duplicates().sort_values(by='TeamPoints', ascending=False)
                
                for _, team_row in sorted_teams.iterrows():
                    team_name = team_row['TeamName']
                    team_points = team_row['TeamPoints']
                    
                    with st.expander(f"**{team_name}** - {int(team_points)} points"):
                        st.subheader("Pilotes de la saison")
                        drivers_df = year_teams_data[year_teams_data['TeamName'] == team_name].sort_values(by='DriverPoints', ascending=False)
                        st.dataframe(
                            drivers_df[['DriverName', 'Abbreviation', 'DriverPoints']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={"DriverName": "Pilote", "Abbreviation": "Code", "DriverPoints": "Points"}
                        )
                        st.caption(f"Cette liste inclut tous les pilotes (y compris les remplaçants) ayant participé pour l'écurie durant la saison.")
            else:
                st.warning(f"Aucune donnée détaillée sur les écuries trouvée pour {selected_year}.")
    
    # Onglet 4 : Progression
    with tabs[3]:
        st.header(f"📈 Progression du Championnat - {selected_year}")
        
        progress_type = st.radio("Afficher la progression pour :", ["Pilotes", "Écuries"], horizontal=True, key="progress_radio")
        
        if not season_data.empty:
            if progress_type == "Pilotes":
                data_to_plot = season_data.copy()
                data_to_plot['CumulativePoints'] = data_to_plot.groupby('driver_code')['points'].cumsum()
                color_column, title_column = 'driver_code', 'Pilote'
            else: # Écuries
                team_points_per_race = season_data.groupby(['round', 'race_name', 'team'])['points'].sum().reset_index()
                team_points_sorted = team_points_per_race.sort_values(by='round')
                data_to_plot = team_points_sorted.copy()
                data_to_plot['CumulativePoints'] = data_to_plot.groupby('team')['points'].cumsum()
                color_column, title_column = 'team', 'Équipe'

            chart = (
                alt.Chart(data_to_plot)
                .mark_line(point=True)
                .encode(
                    x=alt.X("round:O", title="Course"),
                    y=alt.Y("CumulativePoints:Q", title="Points Cumulés"),
                    color=alt.Color(f"{color_column}:N", title=title_column),
                    tooltip=["race_name", color_column, "CumulativePoints"],
                ).interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")

    # Onglet 5 : Prédictions
    with tabs[4]:
        if model is not None:
            st.header("🎯 Simuler une Prédiction")
            st.info("Choisissez une course pour lancer une prédiction basée sur le dernier modèle entraîné.")
            pred_years_available = sorted(full_data['year'].unique(), reverse=True)
            pred_year = st.selectbox("Année pour la prédiction:", options=pred_years_available, key="pred_year")
            available_races = sorted(full_data[full_data['year'] == pred_year]['race_name'].unique())
            
            if available_races:
                selected_race = st.selectbox("Choisissez un Grand Prix:", options=available_races, key="pred_race")
                if st.button(f"Prédire le classement pour le {selected_race} {pred_year}"):
                    with st.spinner(f"Calcul de la prédiction..."):
                        result = run_prediction(model, feature_columns, full_data, pred_year, selected_race)
                    
                    st.subheader("🏆 Classement Prédit vs. Réalité")
                    if isinstance(result, pd.DataFrame):
                        if 'ActualPosition' in result.columns:
                            result['ActualPosition'] = pd.to_numeric(result['ActualPosition'], errors='coerce')
                        display_cols = ['PredictedRank', 'driver_code', 'team', 'grid', 'ActualPosition', 'PredictedPositionValue']
                        cols_to_show = [col for col in display_cols if col in result.columns]
                        st.dataframe(result[cols_to_show], use_container_width=True)
                        if 'ActualPosition' in result.columns:
                            mae_df = result.dropna(subset=['ActualPosition'])
                            if not mae_df.empty:
                                mae = (mae_df['PredictedRank'] - mae_df['ActualPosition']).abs().mean()
                                st.metric(label="Erreur Absolue Moyenne (MAE)", value=f"{mae:.2f}")
                        st.success("Prédiction terminée !")
                    else:
                        st.error(result)
            else:
                st.warning(f"Aucune course trouvée pour l'année {pred_year}.")
