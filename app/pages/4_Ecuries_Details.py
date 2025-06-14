# pages/2_Ecuries_Details.py

import streamlit as st
import pandas as pd
# Assurez-vous que le fichier config.py est au bon endroit
from utils import HISTORICAL_DATA_PATH, TEAMS_DATA_PATH

# --- Configuration de la Page ---
st.set_page_config(
    layout="wide",
    page_title="Détails des Écuries",
    page_icon="🏎️"
)

st.title("🏎️ Détails des Écuries par Saison")
st.markdown("---")


# --- Fonctions de chargement des données (avec cache) ---
# Ces fonctions sont reprises de votre app.py pour que la page soit autonome
@st.cache_data(ttl="6h")
def load_main_dataset():
    """Charge le grand fichier de données F1 pour obtenir la liste des années."""
    try:
        df = pd.read_csv(HISTORICAL_DATA_PATH)
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
        st.error(f"Fichier de données des écuries introuvable ! Assurez-vous que le chemin '{TEAMS_DATA_PATH}' est correct.")
        return None

# --- Chargement des données ---
full_data = load_main_dataset()
teams_summary = load_teams_data()

# --- Barre Latérale (Sidebar) pour les filtres ---
# Le filtre par année est nécessaire pour cette page
if full_data is not None:
    with st.sidebar:
        st.header("Filtres")
        # Permet la sélection de toutes les années disponibles
        display_years = sorted(full_data['year'].unique(), reverse=True)
        selected_year = st.selectbox(
            "Choisissez une année :",
            options=display_years,
            key="year_selector" # Une clé unique est une bonne pratique
        )
else:
    st.sidebar.warning("Données principales non chargées, impossible d'afficher les filtres.")
    # Arrête l'exécution si les données ne sont pas là
    st.stop()


# --- Affichage principal de la page ---
st.header(f"Performance des Écuries en {selected_year}")

if teams_summary is not None:
    # On filtre les données des écuries avec l'année sélectionnée dans la sidebar
    year_teams_data = teams_summary[teams_summary['Year'] == selected_year]

    if not year_teams_data.empty:
        # Trier les écuries par le total de points pour un affichage ordonné
        sorted_teams = year_teams_data[['TeamName', 'TeamPoints']].drop_duplicates().sort_values(
            by='TeamPoints',
            ascending=False
        )
        
        # Créer un expander pour chaque écurie
        for _, team_row in sorted_teams.iterrows():
            team_name = team_row['TeamName']
            team_points = team_row['TeamPoints']
            
            with st.expander(f"**{team_name}** - {int(team_points)} points"):
                st.subheader("Pilotes de la saison")
                
                # Filtrer les données pour l'écurie actuelle et trier les pilotes par points
                drivers_df = year_teams_data[year_teams_data['TeamName'] == team_name].sort_values(
                    by='DriverPoints',
                    ascending=False
                )
                
                # Afficher le DataFrame des pilotes
                st.dataframe(
                    drivers_df[['DriverName', 'Abbreviation', 'DriverPoints']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "DriverName": "Pilote",
                        "Abbreviation": "Code",
                        "DriverPoints": "Points"
                    }
                )
                st.caption("Cette liste inclut tous les pilotes (y compris les remplaçants) ayant participé pour l'écurie durant la saison.")
    else:
        st.warning(f"Aucune donnée détaillée sur les écuries n'a été trouvée pour {selected_year}.")
else:
    st.error("Les données récapitulatives des écuries n'ont pas pu être chargées.")