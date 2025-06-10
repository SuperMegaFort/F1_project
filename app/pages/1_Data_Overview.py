# pages/1_Data_Overview.py
import streamlit as st
import pandas as pd
# Import shared functions and constants from utils.py
from utils import (
    load_data,
    convert_df_to_csv,
    SESSION_FILES,
    YEAR_COLUMN,
    GP_NAME_COLUMN
)

st.set_page_config(
    layout="wide",
    page_title="Data Overview",
    page_icon="🏎️"
)

# --- Page Title ---
st.title("📄 Exploration des Données (Tableau)")
st.markdown("Utilisez les filtres dans la barre latérale pour explorer les données de session.")

# --- Sidebar for filters - specific to this page ---
st.sidebar.header("Filtres pour le Tableau")
selected_session_name_table = st.sidebar.selectbox(
    "Choisissez un type de session",
    list(SESSION_FILES.keys()),
    key="table_session_select"
)

file_to_load_table = SESSION_FILES.get(selected_session_name_table)
df_current_session = load_data(file_to_load_table) if file_to_load_table else pd.DataFrame()

if not df_current_session.empty:
    df_current_session[YEAR_COLUMN] = df_current_session[YEAR_COLUMN].astype(str)
    available_years_table = ["Toutes"] + sorted(df_current_session[YEAR_COLUMN].unique(), reverse=True)
    selected_year_table = st.sidebar.selectbox(
        "Choisissez une année",
        available_years_table,
        key="table_year_select"
    )

    df_filtered_by_year_table = df_current_session.copy()
    if selected_year_table != "Toutes":
        df_filtered_by_year_table = df_current_session[df_current_session[YEAR_COLUMN] == selected_year_table]

    # Grand Prix filter (dependent on year)
    if not df_filtered_by_year_table.empty and GP_NAME_COLUMN in df_filtered_by_year_table.columns:
        available_gp_table = ["Tous"] + sorted(df_filtered_by_year_table[GP_NAME_COLUMN].unique())
        selected_gp_table = st.sidebar.selectbox(
            "Choisissez un Grand Prix",
            available_gp_table,
            key="table_gp_select"
        )

        df_filtered_by_gp_table = df_filtered_by_year_table.copy()
        if selected_gp_table != "Tous":
            df_filtered_by_gp_table = df_filtered_by_year_table[df_filtered_by_year_table[GP_NAME_COLUMN] == selected_gp_table]
    else:
        df_filtered_by_gp_table = df_filtered_by_year_table

    if not df_filtered_by_gp_table.empty:
        all_columns = df_filtered_by_gp_table.columns.tolist()
        default_cols_candidates = [GP_NAME_COLUMN, YEAR_COLUMN, 'driver_name', 'constructor_name', 'position', 'laps', 'time', 'points']
        default_columns = [col for col in default_cols_candidates if col in all_columns]
        if not default_columns and all_columns:
             default_columns = all_columns[:5] if len(all_columns) > 5 else all_columns

        selected_columns_table = st.sidebar.multiselect(
            "Colonnes à afficher",
            all_columns,
            default=default_columns,
            key="table_column_select"
        )
    else:
        selected_columns_table = []

    if not df_filtered_by_gp_table.empty and selected_columns_table:
        st.success(f"Affichage des données pour : Session '{selected_session_name_table}', Année '{selected_year_table}', Grand Prix '{selected_gp_table}'.")
        st.dataframe(df_filtered_by_gp_table[selected_columns_table], use_container_width=True)

        csv_data_table = convert_df_to_csv(df_filtered_by_gp_table[selected_columns_table])
        st.download_button(
           label="📥 Télécharger les données filtrées (CSV)",
           data=csv_data_table,
           file_name=f"{selected_session_name_table}_{selected_year_table}_{selected_gp_table}_filtre.csv".replace(" ", "_").replace("'", ""),
           mime="text/csv",
        )
    elif df_current_session.empty:
         st.info(f"Aucune donnée n'a pu être chargée pour la session '{selected_session_name_table}'. Vérifiez que le fichier '{file_to_load_table}' existe et est correct.")
    elif not selected_columns_table and not df_filtered_by_gp_table.empty :
         st.info("Veuillez sélectionner au moins une colonne à afficher.")
    else:
         st.info("Aucune donnée ne correspond à vos filtres actuels. Essayez d'élargir votre sélection.")
else:
    if file_to_load_table:
        st.error(f"Impossible de charger les données pour la session sélectionnée ({selected_session_name_table}). Assurez-vous que le fichier '{file_to_load_table}' est présent dans le dossier 'data' et qu'il est correct.")
    else:
        st.error("Session sélectionnée non valide ou fichier non spécifié.")  