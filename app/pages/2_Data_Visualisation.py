# pages/2_Data_Visualisation.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
# Import shared functions and constants from utils.py
from utils import (
    load_data,
    SESSION_FILES,
    YEAR_COLUMN,
    GP_NAME_COLUMN,
    VIS_DRIVER_COL,
    VIS_POSITION_COL,
    POINTS_COL,
    CONSTRUCTOR_COL
)

st.set_page_config(
    layout="wide",
    page_title="Data Visualisation",
    page_icon="🏎️"
)

# --- Page Title ---
st.title("📊 Data Visualisation F1")
st.markdown("Choisissez les options ci-dessous pour générer des visualisations spécifiques.")
st.markdown("---")

DF_RACES_GLOBAL = pd.DataFrame()
race_file_path = SESSION_FILES.get("Course")

if race_file_path and os.path.exists(race_file_path):
    DF_RACES_GLOBAL = load_data(race_file_path)
    if not DF_RACES_GLOBAL.empty:
        DF_RACES_GLOBAL[YEAR_COLUMN] = DF_RACES_GLOBAL[YEAR_COLUMN].astype(str) # Standardisation du type année
    else:
        st.warning(f"Le fichier de données des courses ({race_file_path}) est vide. Certains graphiques pourraient ne pas s'afficher.")
else:
    st.error(f"Fichier de données pour les courses ({race_file_path}) non trouvé ou non spécifié dans SESSION_FILES['Course']. Les graphiques de classement annuel ne pourront pas être générés.")

# --- Section 1: Classement Annuel des Pilotes ---
st.subheader("🏆 Classement Annuel des Pilotes")
with st.container(border=True):
    if DF_RACES_GLOBAL.empty:
        st.info("Données de course non disponibles pour générer le classement des pilotes.")
    else:
        # Vérifier les colonnes nécessaires
        required_cols_plot_drivers = [YEAR_COLUMN, VIS_DRIVER_COL, POINTS_COL]
        missing_cols_drivers = [col for col in required_cols_plot_drivers if col not in DF_RACES_GLOBAL.columns]

        if missing_cols_drivers:
            st.warning(
                f"Colonnes manquantes pour le classement des pilotes : **{', '.join(missing_cols_drivers)}**. "
                f"Veuillez vérifier les constantes `VIS_DRIVER_COL` et `POINTS_COL` dans `utils.py` et les données du fichier '{race_file_path}'."
            )
        else:
            available_years_annual = sorted(DF_RACES_GLOBAL[YEAR_COLUMN].unique(), reverse=True)
            selected_year_drivers = st.selectbox(
                "Choisissez une année pour le classement des pilotes",
                available_years_annual,
                key="annual_driver_year_select"
            )

            df_year_drivers = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_drivers].copy()
            df_year_drivers[POINTS_COL] = pd.to_numeric(df_year_drivers[POINTS_COL], errors='coerce').fillna(0)

            driver_standings = df_year_drivers.groupby(VIS_DRIVER_COL)[POINTS_COL].sum().reset_index()
            driver_standings = driver_standings.sort_values(by=POINTS_COL, ascending=False).reset_index(drop=True)

            if driver_standings.empty:
                st.info(f"Aucune donnée de points de pilotes trouvée pour l'année {selected_year_drivers}.")
            else:
                fig_drivers = px.bar(
                    driver_standings,
                    x=VIS_DRIVER_COL,
                    y=POINTS_COL,
                    text_auto=True,
                    title=f"Classement des Pilotes - {selected_year_drivers}",
                    labels={VIS_DRIVER_COL: "Pilote", POINTS_COL: "Total des Points"},
                    color=POINTS_COL,
                    color_continuous_scale=px.colors.sequential.Viridis_r 
                )
                fig_drivers.update_layout(xaxis_title="Pilote", yaxis_title="Total des Points")
                st.plotly_chart(fig_drivers, use_container_width=True)

st.markdown("---")

# --- Section 2: Classement Annuel des Écuries ---
st.subheader("🛠️ Classement Annuel des Écuries")
with st.container(border=True):
    if DF_RACES_GLOBAL.empty:
        st.info("Données de course non disponibles pour générer le classement des écuries.")
    else:
        required_cols_plot_constructors = [YEAR_COLUMN, CONSTRUCTOR_COL, POINTS_COL]
        missing_cols_constructors = [col for col in required_cols_plot_constructors if col not in DF_RACES_GLOBAL.columns]

        if missing_cols_constructors:
            st.warning(
                f"Colonnes manquantes pour le classement des écuries : **{', '.join(missing_cols_constructors)}**. "
                f"Veuillez vérifier les constantes `CONSTRUCTOR_COL` et `POINTS_COL` dans `utils.py` et les données du fichier '{race_file_path}'."
            )
        else:
            if 'available_years_annual' not in locals():
                 available_years_annual = sorted(DF_RACES_GLOBAL[YEAR_COLUMN].unique(), reverse=True)

            selected_year_constructors = st.selectbox(
                "Choisissez une année pour le classement des écuries",
                available_years_annual,
                key="annual_constructor_year_select"
            )

            df_year_constructors = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_constructors].copy()
            df_year_constructors[POINTS_COL] = pd.to_numeric(df_year_constructors[POINTS_COL], errors='coerce').fillna(0)

            constructor_standings = df_year_constructors.groupby(CONSTRUCTOR_COL)[POINTS_COL].sum().reset_index()
            constructor_standings = constructor_standings.sort_values(by=POINTS_COL, ascending=False).reset_index(drop=True)

            if constructor_standings.empty:
                st.info(f"Aucune donnée de points d'écuries trouvée pour l'année {selected_year_constructors}.")
            else:
                fig_constructors = px.bar(
                    constructor_standings,
                    x=CONSTRUCTOR_COL,
                    y=POINTS_COL,
                    text_auto=True,
                    title=f"Classement des Écuries - {selected_year_constructors}",
                    labels={CONSTRUCTOR_COL: "Écurie", POINTS_COL: "Total des Points"},
                    color=POINTS_COL,
                    color_continuous_scale=px.colors.sequential.Plasma_r
                )
                fig_constructors.update_layout(xaxis_title="Écurie", yaxis_title="Total des Points")
                st.plotly_chart(fig_constructors, use_container_width=True)

st.markdown("---")

# --- Section 3: Classement d'un Pilote par Année et Session ---
st.subheader("📈 Performance d'un Pilote (Course par Course)")
with st.container(border=True):
    vis_session_options_perf = list(SESSION_FILES.keys())
    col_perf1, col_perf2, col_perf3 = st.columns(3)

    with col_perf1:
        selected_session_perf = st.selectbox(
            "1. Choisissez une session",
            vis_session_options_perf,
            key="driver_race_perf_session_select"
        )

    file_to_load_perf = SESSION_FILES.get(selected_session_perf)
    df_session_perf = pd.DataFrame()
    
    if file_to_load_perf:
        df_session_perf = load_data(file_to_load_perf)

    if not df_session_perf.empty:
        required_cols_plot_perf = [YEAR_COLUMN, GP_NAME_COLUMN, VIS_DRIVER_COL, VIS_POSITION_COL]
        missing_cols_perf = [col for col in required_cols_plot_perf if col not in df_session_perf.columns]

        if missing_cols_perf:
            st.warning(
                f"Pour la session '{selected_session_perf}', colonnes manquantes pour ce graphique : **{', '.join(missing_cols_perf)}**."
                f"\nColonnes requises: `YEAR_COLUMN`, `GP_NAME_COLUMN`, `VIS_DRIVER_COL`, `VIS_POSITION_COL` (vérifiez `utils.py`)."
            )
        else:
            df_session_perf[YEAR_COLUMN] = df_session_perf[YEAR_COLUMN].astype(str)
            available_years_perf = sorted(df_session_perf[YEAR_COLUMN].unique(), reverse=True)
            
            with col_perf2:
                selected_year_perf = st.selectbox(
                    "2. Choisissez une année",
                    available_years_perf,
                    key="driver_race_perf_year_select"
                )
            
            df_year_filtered_perf = df_session_perf[df_session_perf[YEAR_COLUMN] == selected_year_perf]

            if not df_year_filtered_perf.empty:
                available_drivers_perf = sorted(df_year_filtered_perf[VIS_DRIVER_COL].dropna().unique())
                
                if not available_drivers_perf:
                    st.info(f"Aucun pilote trouvé pour l'année {selected_year_perf} dans la session '{selected_session_perf}'.")
                else:
                    with col_perf3:
                        selected_driver_perf = st.selectbox(
                            "3. Choisissez un pilote",
                            available_drivers_perf,
                            key="driver_race_perf_driver_select"
                        )
                    
                    df_driver_filtered_perf = df_year_filtered_perf[df_year_filtered_perf[VIS_DRIVER_COL] == selected_driver_perf]

                    if not df_driver_filtered_perf.empty:
                        df_plot_data_perf = df_driver_filtered_perf.copy()
                        df_plot_data_perf[VIS_POSITION_COL] = pd.to_numeric(df_plot_data_perf[VIS_POSITION_COL], errors='coerce')
                        df_plot_data_perf = df_plot_data_perf.sort_values(by=GP_NAME_COLUMN)

                        if not df_plot_data_perf.dropna(subset=[VIS_POSITION_COL]).empty:
                            fig_perf = px.line(
                                df_plot_data_perf,
                                x=GP_NAME_COLUMN,
                                y=VIS_POSITION_COL,
                                title=f"Performance de {selected_driver_perf} ({selected_year_perf}) - Session: {selected_session_perf}",
                                markers=True,
                                labels={VIS_POSITION_COL: "Position", GP_NAME_COLUMN: "Grand Prix"}
                            )
                            fig_perf.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_perf, use_container_width=True)
                        else:
                            st.info(f"Aucune donnée de position numérique à afficher pour {selected_driver_perf} en {selected_year_perf} (Session: {selected_session_perf}).")
                    else:
                        st.info(f"Aucune donnée pour le pilote {selected_driver_perf} en {selected_year_perf} pour la session '{selected_session_perf}'.")
            else:
                st.info(f"Aucune donnée pour l'année {selected_year_perf} dans la session '{selected_session_perf}'.")
    elif file_to_load_perf:
        st.warning(f"Aucune donnée n'a pu être chargée pour la session '{selected_session_perf}' pour le graphique de performance.")

st.markdown("---")
# Emplacement pour d'éventuels futurs autres graphiques
st.subheader("🧩 Plus de Visualisations (à venir)")
with st.container(border=True):
    st.markdown("Cette section pourra accueillir d'autres types de graphiques.")
