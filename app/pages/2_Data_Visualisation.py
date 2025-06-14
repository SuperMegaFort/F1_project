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

# --- Data Loading ---
@st.cache_data
def load_race_data():
    race_file_path = SESSION_FILES.get("Course")
    if race_file_path and os.path.exists(race_file_path):
        df = load_data(race_file_path)
        if not df.empty:
            df[YEAR_COLUMN] = df[YEAR_COLUMN].astype(str)
        return df
    return pd.DataFrame()

DF_RACES_GLOBAL = load_race_data()

if DF_RACES_GLOBAL.empty:
    st.error(f"Fichier de données pour les courses non trouvé ou vide. Les visualisations ne peuvent pas être générées.")
    st.stop()

available_years_annual = sorted(DF_RACES_GLOBAL[YEAR_COLUMN].unique(), reverse=True)

# --- Tab Layout ---
tab_drivers, tab_constructors = st.tabs(["🏎️ Données Pilotes", "🛠️ Données Écuries"])

# --- DRIVERS TAB ---
with tab_drivers:
    st.header("Visualisations Centrées sur les Pilotes")

    # --- Section 1: Classement Annuel des Pilotes ---
    st.subheader("🏆 Classement Annuel des Pilotes")
    with st.container(border=True):
        selected_year_drivers = st.selectbox(
            "Choisissez une année pour le classement des pilotes",
            available_years_annual,
            key="annual_driver_year_select"
        )
        df_year_drivers = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_drivers].copy()
        df_year_drivers[POINTS_COL] = pd.to_numeric(df_year_drivers[POINTS_COL], errors='coerce').fillna(0)
        driver_standings = df_year_drivers.groupby(VIS_DRIVER_COL)[POINTS_COL].sum().sort_values(ascending=False).reset_index()

        if not driver_standings.empty:
            fig_drivers = px.bar(
                driver_standings, x=VIS_DRIVER_COL, y=POINTS_COL, text_auto=True,
                title=f"Classement des Pilotes - {selected_year_drivers}",
                labels={VIS_DRIVER_COL: "Pilote", POINTS_COL: "Total des Points"},
                color=POINTS_COL, color_continuous_scale=px.colors.sequential.Viridis_r
            )
            st.plotly_chart(fig_drivers, use_container_width=True)
        else:
            st.info(f"Aucune donnée de points de pilotes trouvée pour l'année {selected_year_drivers}.")
    
    st.markdown("---")

    # --- Section 2: Progression du Championnat (Pilotes) ---
    st.subheader("📈 Progression du Championnat des Pilotes")
    with st.container(border=True):
        selected_year_prog_d = st.selectbox("Choisissez une année", available_years_annual, key="prog_year_select_d")
        df_prog_d = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_prog_d].copy()
        df_prog_d[POINTS_COL] = pd.to_numeric(df_prog_d[POINTS_COL], errors='coerce').fillna(0)
        df_prog_d['CumulativePoints'] = df_prog_d.groupby(VIS_DRIVER_COL)[POINTS_COL].cumsum()

        if not df_prog_d.empty:
            fig_prog_d = px.line(
                df_prog_d, x=GP_NAME_COLUMN, y='CumulativePoints', color=VIS_DRIVER_COL, markers=True,
                title=f"Progression des Points des Pilotes - {selected_year_prog_d}",
                labels={'CumulativePoints': 'Points Cumulés', GP_NAME_COLUMN: 'Grand Prix', VIS_DRIVER_COL: 'Pilote'}
            )
            st.plotly_chart(fig_prog_d, use_container_width=True)
        else:
            st.info(f"Pas de données pour afficher la progression des pilotes en {selected_year_prog_d}.")

    st.markdown("---")
    
    # --- Section 3: Distribution des Positions (Pilotes) ---
    st.subheader("📊 Distribution des Positions des Pilotes")
    with st.container(border=True):
        selected_year_dist_d = st.selectbox("Choisissez une année", available_years_annual, key="dist_year_select_d")
        df_dist_d = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_dist_d].copy()
        df_dist_d[VIS_POSITION_COL] = pd.to_numeric(df_dist_d[VIS_POSITION_COL], errors='coerce')
        df_dist_d.dropna(subset=[VIS_POSITION_COL], inplace=True)
        df_dist_d[VIS_POSITION_COL] = df_dist_d[VIS_POSITION_COL].astype(int)

        if not df_dist_d.empty:
            sorted_order_d = df_dist_d.groupby(VIS_DRIVER_COL)[VIS_POSITION_COL].median().sort_values().index
            fig_dist_d = px.box(
                df_dist_d, x=VIS_DRIVER_COL, y=VIS_POSITION_COL, color=VIS_DRIVER_COL,
                title=f"Distribution des Positions en Course (Pilotes) - {selected_year_dist_d}",
                labels={VIS_DRIVER_COL: "Pilote", VIS_POSITION_COL: "Position Finale"},
                category_orders={VIS_DRIVER_COL: sorted_order_d}
            )
            fig_dist_d.update_layout(yaxis=dict(autorange="reversed"), xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig_dist_d, use_container_width=True)
        else:
            st.info(f"Aucune donnée de position valide à afficher pour les pilotes en {selected_year_dist_d}.")
            
    st.markdown("---")

    # --- Section 4: Performance d'un Pilote par Année et Session ---
    st.subheader("🏎️ Performance d'un Pilote (Course par Course)")
    with st.container(border=True):
        vis_session_options_perf = list(SESSION_FILES.keys())
        col_perf1, col_perf2, col_perf3 = st.columns(3)

        with col_perf1:
            selected_session_perf = st.selectbox("1. Choisissez une session", vis_session_options_perf, key="driver_perf_session")
        
        file_to_load_perf = SESSION_FILES.get(selected_session_perf)
        if file_to_load_perf and os.path.exists(file_to_load_perf):
            df_session_perf = load_data(file_to_load_perf)
            df_session_perf[YEAR_COLUMN] = df_session_perf[YEAR_COLUMN].astype(str)
            available_years_perf = sorted(df_session_perf[YEAR_COLUMN].unique(), reverse=True)

            with col_perf2:
                selected_year_perf = st.selectbox("2. Choisissez une année", available_years_perf, key="driver_perf_year")
            
            df_year_filtered_perf = df_session_perf[df_session_perf[YEAR_COLUMN] == selected_year_perf]
            available_drivers_perf = sorted(df_year_filtered_perf[VIS_DRIVER_COL].dropna().unique())

            if available_drivers_perf:
                with col_perf3:
                    selected_driver_perf = st.selectbox("3. Choisissez un pilote", available_drivers_perf, key="driver_perf_driver")
                
                df_driver_filtered_perf = df_year_filtered_perf[df_year_filtered_perf[VIS_DRIVER_COL] == selected_driver_perf]                
                df_driver_filtered_perf.loc[:, VIS_POSITION_COL] = pd.to_numeric(df_driver_filtered_perf[VIS_POSITION_COL], errors='coerce')

                if not df_driver_filtered_perf.dropna(subset=[VIS_POSITION_COL]).empty:
                    fig_perf = px.line(
                        df_driver_filtered_perf.sort_values(by=GP_NAME_COLUMN),
                        x=GP_NAME_COLUMN, y=VIS_POSITION_COL, markers=True,
                        title=f"Performance de {selected_driver_perf} ({selected_year_perf}) - Session: {selected_session_perf}",
                        labels={VIS_POSITION_COL: "Position", GP_NAME_COLUMN: "Grand Prix"}
                    )
                    fig_perf.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig_perf, use_container_width=True)
                else:
                    st.info(f"Aucune donnée de position pour {selected_driver_perf} en {selected_year_perf}.")
            else:
                st.info(f"Aucun pilote trouvé pour {selected_year_perf} dans la session '{selected_session_perf}'.")
        else:
            st.warning(f"Données pour la session '{selected_session_perf}' non trouvées.")


# --- CONSTRUCTORS TAB ---
with tab_constructors:
    st.header("Visualisations Centrées sur les Écuries")

    # --- Section 1: Classement Annuel des Écuries ---
    st.subheader("🛠️ Classement Annuel des Écuries")
    with st.container(border=True):
        selected_year_constructors = st.selectbox(
            "Choisissez une année pour le classement des écuries",
            available_years_annual,
            key="annual_constructor_year_select"
        )
        df_year_constructors = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_constructors].copy()
        df_year_constructors[POINTS_COL] = pd.to_numeric(df_year_constructors[POINTS_COL], errors='coerce').fillna(0)
        constructor_standings = df_year_constructors.groupby(CONSTRUCTOR_COL)[POINTS_COL].sum().sort_values(ascending=False).reset_index()

        if not constructor_standings.empty:
            fig_constructors = px.bar(
                constructor_standings, x=CONSTRUCTOR_COL, y=POINTS_COL, text_auto=True,
                title=f"Classement des Écuries - {selected_year_constructors}",
                labels={CONSTRUCTOR_COL: "Écurie", POINTS_COL: "Total des Points"},
                color=POINTS_COL, color_continuous_scale=px.colors.sequential.Plasma_r
            )
            st.plotly_chart(fig_constructors, use_container_width=True)
        else:
            st.info(f"Aucune donnée de points d'écuries trouvée pour l'année {selected_year_constructors}.")

    st.markdown("---")
    
    # --- Section 2: Progression du Championnat (Écuries) ---
    st.subheader("📈 Progression du Championnat des Écuries")
    with st.container(border=True):
        selected_year_prog_c = st.selectbox("Choisissez une année", available_years_annual, key="prog_year_select_c")
        df_prog_c = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_prog_c].copy()
        df_prog_c[POINTS_COL] = pd.to_numeric(df_prog_c[POINTS_COL], errors='coerce').fillna(0)
        
        team_points_per_race = df_prog_c.groupby([GP_NAME_COLUMN, CONSTRUCTOR_COL])[POINTS_COL].sum().reset_index()
        team_points_per_race['CumulativePoints'] = team_points_per_race.groupby(CONSTRUCTOR_COL)[POINTS_COL].cumsum()

        if not team_points_per_race.empty:
            fig_prog_c = px.line(
                team_points_per_race, x=GP_NAME_COLUMN, y='CumulativePoints', color=CONSTRUCTOR_COL, markers=True,
                title=f"Progression des Points des Écuries - {selected_year_prog_c}",
                labels={'CumulativePoints': 'Points Cumulés', GP_NAME_COLUMN: 'Grand Prix', CONSTRUCTOR_COL: 'Écurie'}
            )
            st.plotly_chart(fig_prog_c, use_container_width=True)
        else:
            st.info(f"Pas de données pour afficher la progression des écuries en {selected_year_prog_c}.")
            
    st.markdown("---")
    
    # --- Section 3: Distribution des Positions (Écuries) ---
    st.subheader("📊 Distribution des Positions des Écuries")
    with st.container(border=True):
        selected_year_dist_c = st.selectbox("Choisissez une année", available_years_annual, key="dist_year_select_c")
        df_dist_c = DF_RACES_GLOBAL[DF_RACES_GLOBAL[YEAR_COLUMN] == selected_year_dist_c].copy()
        df_dist_c[VIS_POSITION_COL] = pd.to_numeric(df_dist_c[VIS_POSITION_COL], errors='coerce')
        df_dist_c.dropna(subset=[VIS_POSITION_COL], inplace=True)
        df_dist_c[VIS_POSITION_COL] = df_dist_c[VIS_POSITION_COL].astype(int)

        if not df_dist_c.empty:
            sorted_order_c = df_dist_c.groupby(CONSTRUCTOR_COL)[VIS_POSITION_COL].median().sort_values().index
            fig_dist_c = px.box(
                df_dist_c, x=CONSTRUCTOR_COL, y=VIS_POSITION_COL, color=CONSTRUCTOR_COL,
                title=f"Distribution des Positions en Course (Écuries) - {selected_year_dist_c}",
                labels={CONSTRUCTOR_COL: "Écurie", VIS_POSITION_COL: "Position Finale"},
                category_orders={CONSTRUCTOR_COL: sorted_order_c}
            )
            fig_dist_c.update_layout(yaxis=dict(autorange="reversed"), xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig_dist_c, use_container_width=True)
        else:
            st.info(f"Aucune donnée de position valide à afficher pour les écuries en {selected_year_dist_c}.")
