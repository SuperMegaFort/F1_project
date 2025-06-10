# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from config import ALL_DATA_PATH
from prediction_logic import run_prediction

# --- Configuration de la Page et du Style ---
st.set_page_config(page_title="F1 Vision", layout="wide", initial_sidebar_state="expanded")

# Injection de CSS pour un design personnalisé
st.markdown("""
<style>
    /* Thème général sombre */
    .main {
        background-color: #121212;
        color: #EAEAEA;
    }
    h1, h2, h3 {
        color: #FFFFFF;
    }
    
    /* Barre latérale */
    [data-testid="stSidebar"] {
        background-color: #0A0A0A;
    }
    
    /* Boutons et éléments interactifs */
    .stButton>button {
        background-color: #e10600;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FF1900;
        color: white;
    }
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {
		gap: 24px;
	}
    .stTabs [data-baseweb="tab"] {
		height: 50px;
        background-color: transparent;
		border-radius: 4px 4px 0px 0px;
		padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #e10600;
    }
    
</style>
""", unsafe_allow_html=True)


# --- Fonction pour charger les données (avec cache pour la performance) ---
@st.cache_data(ttl="6h")
def load_main_dataset():
    """Charge le grand fichier de données F1 et le prépare."""
    try:
        df = pd.read_csv(ALL_DATA_PATH)
        # On génère la colonne 'round' si elle n'existe pas
        if 'round' not in df.columns:
            df['race_id'] = pd.to_numeric(df['race_id'], errors='coerce').dropna().astype(int)
            rounds_map = df[['year', 'race_id']].drop_duplicates().sort_values(by=['year', 'race_id'])
            rounds_map['round'] = rounds_map.groupby('year').cumcount() + 1
            df = pd.merge(df, rounds_map[['race_id', 'round']], on='race_id', how='left')
        return df
    except FileNotFoundError:
        return None

# --- Application Principale ---

# Titre principal
st.markdown("<h1 style='text-align: center; font-weight: bold;'>F1 VISION DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("---")

# Charger les données une seule fois
full_data = load_main_dataset()

if full_data is None:
    st.error(f"Dataset principal non trouvé ! Assurez-vous que le fichier '{ALL_DATA_PATH}' existe.")
else:
    # --- Barre Latérale (Sidebar) pour le filtre d'année ---
    with st.sidebar:
        st.image("https://www.formula1.com/etc/designs/fom-website/images/f1_logo.svg", width=100)
        st.header("Filtres")
        available_years = sorted(full_data['year'].unique(), reverse=True)
        selected_year = st.selectbox("Choisissez une année :", options=available_years)

    # Filtrer les données pour l'année sélectionnée
    season_data = full_data[full_data['year'] == selected_year].copy()

    # --- Définition des Onglets ---
    tab_drivers, tab_constructors, tab_progress, tab_predictions = st.tabs([
        "🏆 Classement Pilotes", 
        "🛠️ Classement Constructeurs", 
        "📈 Progression", 
        "🎯 Prédictions"
    ])

    # --- Onglet 1 : Classement des Pilotes ---
    with tab_drivers:
        st.header(f"🏆 Classement Final des Pilotes - {selected_year}")
        if not season_data.empty:
            driver_standings = season_data.groupby(['driver_code', 'team'])['points'].sum().reset_index()
            driver_standings = driver_standings.sort_values(by='points', ascending=False).reset_index(drop=True)
            driver_standings['Position'] = driver_standings.index + 1
            st.dataframe(driver_standings[['Position', 'driver_code', 'team', 'points']], use_container_width=True)
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")

    # --- Onglet 2 : Classement des Constructeurs ---
    with tab_constructors:
        st.header(f"🛠️ Classement Final des Constructeurs - {selected_year}")
        if not season_data.empty:
            constructor_standings = season_data.groupby('team')['points'].sum().reset_index()
            constructor_standings = constructor_standings.sort_values(by='points', ascending=False).reset_index(drop=True)
            constructor_standings['Position'] = constructor_standings.index + 1
            st.dataframe(constructor_standings[['Position', 'team', 'points']], use_container_width=True)
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")

    # --- Onglet 3 : Progression du Championnat ---
    with tab_progress:
        st.header(f"📈 Progression du Championnat - {selected_year}")
        
        # Choix entre Pilotes et Écuries
        progress_type = st.radio("Afficher la progression pour :", ["Pilotes", "Écuries"], horizontal=True)
        
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

    # --- Onglet 4 : Prédictions ---
    with tab_predictions:
        st.header("🎯 Simuler une Prédiction")
        st.info("Choisissez une course de 2025 pour lancer une prédiction basée sur le modèle entraîné sur les données 2020-2024.")
        
        data_2025 = full_data[full_data['year'] == 2025]
        if not data_2025.empty:
            available_races_2025 = sorted(data_2025['race_name'].unique())
            selected_race = st.selectbox("Choisissez un Grand Prix de 2025:", options=available_races_2025)

            if st.button(f"Prédire le classement pour le {selected_race} 2025"):
                with st.spinner(f"Calcul de la prédiction..."):
                    
                    # ## CORRECTION : On passe bien les 3 arguments attendus ##
                    result = run_prediction(full_data, 2025, selected_race)
                
                st.subheader("🏆 Classement Prédit")
                if isinstance(result, pd.DataFrame):
                    st.dataframe(result[['PredictedRank', 'driver_code', 'team', 'grid', 'PredictedPositionValue']])
                    st.success("Prédiction terminée !")
                else:
                    st.error(result)
        else:
            st.warning("Aucune donnée pour la saison 2025 trouvée dans le fichier principal.")

