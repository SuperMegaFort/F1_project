import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Analyse Données F1")

st.title("🏎️ Visualisation des Données de Formule 1")
st.markdown("Utilisez les filtres dans la barre latérale pour explorer les données.")

SESSION_FILES = {
    "Course": "data/f1_2015-2024_race.csv",
    "Qualifications": "data/f1_2015-2024_qualifying.csv",
    "Essais Libres 1": "data/f1_2015-2024_practice_1.csv",
    "Essais Libres 2": "data/f1_2015-2024_practice_2.csv",
    "Essais Libres 3": "data/f1_2015-2024_practice_3.csv",
    "Meilleur Tour en Course": "data/f1_2015-2024_fastest_lap.csv",
    "Arrêts aux Stands": "data/f1_2015-2024_pit_stop.csv",
    "Grille de Départ": "data/f1_2015-2024_starting_grid.csv"
}

YEAR_COLUMN = 'year'
GP_NAME_COLUMN = 'race_name'

@st.cache_data
def load_data(file_path):
    """Charge les données depuis un fichier CSV."""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)            
            if YEAR_COLUMN in df.columns:
                df[YEAR_COLUMN] = pd.to_numeric(df[YEAR_COLUMN], errors='coerce')
            return df
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier {file_path}: {e}")
            return pd.DataFrame()
    else:
        st.warning(f"Le fichier {file_path} est introuvable.")
        return pd.DataFrame()

# --- BARRE LATÉRALE POUR LES FILTRES ---
st.sidebar.header("⚙️ Filtres de Sélection")

# 1. Sélection du type de session
selected_session_name = st.sidebar.selectbox(
    "Choisissez le type de session :",
    options=list(SESSION_FILES.keys())
)

# Charger les données pour la session sélectionnée
file_to_load = SESSION_FILES.get(selected_session_name)
df_current_session = pd.DataFrame()

if file_to_load:
    df_current_session = load_data(file_to_load)
else:
    st.sidebar.error("Type de session non valide sélectionné.")

# Vérifier si les données ont été chargées et si les colonnes clés existent
if not df_current_session.empty:
    if YEAR_COLUMN not in df_current_session.columns:
        st.sidebar.warning(f"La colonne '{YEAR_COLUMN}' est manquante dans {file_to_load}. Le filtrage par année pourrait ne pas fonctionner.")
    if GP_NAME_COLUMN not in df_current_session.columns:
        st.sidebar.warning(f"La colonne '{GP_NAME_COLUMN}' est manquante dans {file_to_load}. Le filtrage par Grand Prix pourrait ne pas fonctionner.")

    # 2. Sélection de l'année
    available_years = []
    if YEAR_COLUMN in df_current_session.columns:
        available_years = sorted(df_current_session[YEAR_COLUMN].dropna().unique().astype(int), reverse=True)
    
    selected_years = []
    if available_years:
        selected_years = st.sidebar.multiselect(
            "Choisissez l'année(s) :",
            options=available_years,
            default=available_years[0] if available_years else [] # Sélectionne la plus récente par défaut
        )
    else:
        st.sidebar.text("Aucune donnée d'année disponible pour cette session.")

    # Filtrer les données par année sélectionnée pour populer les GP
    df_filtered_by_year = df_current_session.copy()
    if selected_years and YEAR_COLUMN in df_filtered_by_year.columns:
        df_filtered_by_year = df_filtered_by_year[df_filtered_by_year[YEAR_COLUMN].isin(selected_years)]

    # 3. Sélection du Grand Prix
    available_gp_names = []
    if GP_NAME_COLUMN in df_filtered_by_year.columns:
        available_gp_names = sorted(df_filtered_by_year[GP_NAME_COLUMN].dropna().unique())
    
    selected_gp_names = []
    if available_gp_names:
        selected_gp_names = st.sidebar.multiselect(
            "Choisissez le/les Grand Prix :",
            options=available_gp_names,
            default=available_gp_names if len(available_gp_names) < 10 else available_gp_names[:3] # Sélectionne tous si peu, sinon les 3 premiers
        )
    else:
        st.sidebar.text("Aucun nom de GP disponible pour cette sélection.")

    # Filtrer les données par GP sélectionné
    df_filtered_by_gp = df_filtered_by_year.copy()
    if selected_gp_names and GP_NAME_COLUMN in df_filtered_by_gp.columns:
        df_filtered_by_gp = df_filtered_by_gp[df_filtered_by_gp[GP_NAME_COLUMN].isin(selected_gp_names)]

    # 4. Sélection des colonnes à afficher
    available_columns = df_filtered_by_gp.columns.tolist()
    
    # Exclure par défaut certaines colonnes si elles existent (ex: index inutiles)
    default_columns_to_exclude = ['Unnamed: 0', 'index'] 
    default_selected_columns = [col for col in available_columns if col not in default_columns_to_exclude]

    selected_columns = []
    if available_columns:
        selected_columns = st.sidebar.multiselect(
            "Choisissez les informations à afficher :",
            options=available_columns,
            default=default_selected_columns
        )
    else:
        st.sidebar.text("Aucune colonne disponible.")

    # --- AFFICHAGE DES DONNÉES FILTRÉES ---
    st.subheader(f"Données pour : {selected_session_name}")

    if not df_filtered_by_gp.empty and selected_columns:
        # Afficher le nombre de lignes résultantes
        st.markdown(f"**{len(df_filtered_by_gp)} lignes trouvées pour votre sélection.**")
        
        # Afficher le DataFrame
        st.dataframe(df_filtered_by_gp[selected_columns], use_container_width=True)
        
        # Option pour télécharger les données filtrées
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        csv_data = convert_df_to_csv(df_filtered_by_gp[selected_columns])
        st.download_button(
           label="📥 Télécharger les données filtrées (CSV)",
           data=csv_data,
           file_name=f"{selected_session_name}_filtre.csv",
           mime="text/csv",
        )

    elif df_current_session.empty:
        st.info(f"Aucune donnée n'a pu être chargée pour la session '{selected_session_name}'. Vérifiez que le fichier '{file_to_load}' existe et est correct.")
    elif not selected_columns:
        st.info("Veuillez sélectionner au moins une colonne à afficher.")
    else:
        st.info("Aucune donnée ne correspond à vos filtres actuels. Essayez d'élargir votre sélection.")

else:
    if file_to_load:
        st.error(f"Impossible de charger les données pour la session sélectionnée ({selected_session_name}). Assurez-vous que le fichier '{file_to_load}' est présent dans le même dossier que le script et qu'il est lisible.")
    else:
        st.info("Veuillez sélectionner un type de session dans la barre latérale.")

st.sidebar.markdown("---")
st.sidebar.markdown("Application développée avec Streamlit.")
