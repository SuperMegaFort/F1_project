# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from config import ALL_DATA_PATH
from prediction_logic import run_prediction
import plotly.express as px

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
        background-color: #B00000;
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
            
            # Create the bar chart using Streamlit's built-in chart
            chart_data = driver_standings.sort_values(by='points', ascending=False).set_index('driver_code')['points'].reset_index()
            fig = px.bar(
                chart_data, 
                x='driver_code', 
                y='points',
                title=f'Points des Pilotes - {selected_year}',
                labels={'driver_code': 'Pilote', 'points': 'Points'},
                color='points',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
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
            
            chart_data = constructor_standings.sort_values(by='points', ascending=False).set_index('team')['points'].reset_index()
            fig = px.bar(
                chart_data, 
                x='team', 
                y='points',
                title=f'Points des Écuries - {selected_year}',
                labels={'team': 'Écurie', 'points': 'Points'},
                color='points',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")

    # --- Onglet 3 : Progression du Championnat ---
    with tab_progress:
        st.header(f"📈 Progression du Championnat - {selected_year}")
        
        st.subheader("🏁 Points cumulés")
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

        st.subheader("3️⃣ Nombre de podiums")
        progress_type = st.radio("Afficher le nombre de podiums pour :", ["Pilotes", "Écuries"], horizontal=True)
        
        if not season_data.empty:
            data_to_plot = season_data.copy()
            data_to_plot['position'] = data_to_plot['position'].replace(['NC', 'DQ'], 1000)
            data_to_plot['position'] = data_to_plot['position'].astype(int)
            data_to_plot['is_podium'] = data_to_plot['position'] <= 3
            
            if progress_type == "Pilotes":
                data_to_plot = data_to_plot[['driver_code', 'is_podium']].groupby('driver_code').sum().reset_index()
                color_column, title_column = 'driver_code', 'Pilote'
            else:
                data_to_plot = data_to_plot[['team', 'is_podium']].groupby('team').sum().reset_index()
                color_column, title_column = 'team', 'Équipe'

            chart = (
                alt.Chart(data_to_plot)
                .mark_bar()
                .encode(
                    x=alt.X(color_column+':N', title=title_column, axis=alt.Axis(labelAngle=-45), 
                    sort=alt.SortField(field=color_column, order='ascending')),
                    y=alt.Y('is_podium:Q', title='Nombre de podiums'),
                    color=alt.Color(color_column+':N', title=title_column),
                )
                .properties(width=400, height=400, title=f'Nombre de podiums - {selected_year}')
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning(f"Aucune donnée disponible pour l'année {selected_year}.")
        
        st.subheader("📊 Résumé des classements")
        # violin plot of the distribution of the positions
        progress_type = st.radio("Afficher la distribution des positions pour :", ["Pilotes", "Écuries"], horizontal=True)
        if not season_data.empty:
            data_to_plot = season_data.copy()
            # drop columns if position is NQ or DQ
            data_to_plot = data_to_plot[data_to_plot['position'] != 'NC']
            data_to_plot = data_to_plot[data_to_plot['position'] != 'DQ']
            # drop columns if position is not a number
            data_to_plot['position'] = pd.to_numeric(data_to_plot['position'], errors='coerce')
            data_to_plot = data_to_plot.dropna(subset=['position'])

            if progress_type == "Pilotes":
                color_column, title_column = 'driver_code', 'Pilote'
            else:
                color_column, title_column = 'team', 'Équipe'

                    # Get the actual range of positions in your data
            min_pos = int(data_to_plot['position'].min())
            max_pos = int(data_to_plot['position'].max())
            
            fig = px.box(
                data_to_plot, 
                x=color_column, 
                y='position',
                title=f'Distribution des positions - {selected_year}',
                labels={color_column: title_column, 'position': 'Position'},
                color=color_column
            )
            
            # Customize the plot
            fig.update_layout(
                yaxis=dict(autorange='reversed'),  # Reverse Y-axis so position 1 is at top
                xaxis_tickangle=-45,
                height=500,
                showlegend=False
            )
                    
            # Display the plot
            st.plotly_chart(fig, use_container_width=True)
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
                    result = run_prediction(full_data, 2025, selected_race)
                
                st.subheader("🏆 Classement Prédit vs. Réalité")
                if isinstance(result, pd.DataFrame):
                    
                    # --- CORRECTION APPLIQUÉE ICI ---
                    # On s'assure que la colonne de la position réelle est numérique avant de calculer l'erreur
                    if 'ActualPosition' in result.columns:
                        result['ActualPosition'] = pd.to_numeric(result['ActualPosition'], errors='coerce')
                    
                    display_cols = ['driver_code', 'team', 'grid', 'ActualPosition', 'PredictedRank', 'PredictedPositionValue']
                    cols_to_show = [col for col in display_cols if col in result.columns]
                    st.dataframe(result[cols_to_show])
                    
                    # Le calcul du MAE ne se fera que sur les lignes où la position réelle est un nombre
                    if 'ActualPosition' in result.columns:
                        mae_df = result.dropna(subset=['ActualPosition'])
                        mae = (mae_df['PredictedRank'] - mae_df['ActualPosition']).abs().mean()
                        st.metric(
                            label="Erreur Absolue Moyenne (MAE)", 
                            value=f"{mae:.2f}",
                            help="La différence moyenne entre le rang prédit et le rang réel (calculée uniquement sur les pilotes classés)."
                        )
                    
                    st.success("Prédiction terminée !")
                else:
                    st.error(result)
                
                col1, col2 = st.columns(2, gap='medium')
                with col1:
                    # actual rank vs predicted rank charts
                    st.subheader("📊 Comparaison Positions Réelles vs Positions Relatives Prédites")
                    chart_data = result[['driver_code', 'team', 'ActualPosition', 'PredictedRank']].copy()
                    chart_data = chart_data.dropna(subset=['ActualPosition', 'PredictedRank'])
                    
                    if not chart_data.empty:
                        # Créer le graphique côte à côte
                        chart = (
                                alt.Chart(chart_data)
                                .mark_bar(opacity=0.7)
                                .encode(
                                    x=alt.X('driver_code:N', title='Pilote', axis=alt.Axis(labelAngle=-45), 
                                    sort=alt.SortField(field='ActualPosition', order='ascending')),
                                    y=alt.Y('value:Q', title='Position', scale=alt.Scale(reverse=True)),
                                    color=alt.Color('variable:N',
                                                title='Type de Position',
                                                scale=alt.Scale(domain=['ActualPosition', 'PredictedRank'],
                                                                range=['#00FA9A', '#1f77b4'])),
                                    xOffset=alt.XOffset('variable:N'),  # This creates the grouped bars
                                    tooltip=['driver_code', 'team', 'ActualPosition', 'PredictedRank']
                                )
                                .transform_fold(
                                    ['ActualPosition', 'PredictedRank'],
                                    as_=['variable', 'value']
                                )
                                .properties(
                                    width=400,  # Adjust overall width
                                    height=400,
                                    title=f'{selected_race} 2025'
                                )
                                .resolve_scale(
                                    color='independent'
                                )
                            )

                        st.altair_chart(chart, use_container_width=True)
                        
                        # Légende explicative
                        st.markdown("""
                        **Légende :**
                        - 🟢 **Vert** : Position réelle
                        - 🔵 **Bleu** : Position prédite
                        - Plus la barre est haute, meilleure est la position (1 = 1er, 20 = 20ème)
                        """)
                    else:
                        st.warning("Aucune donnée de position réelle disponible pour créer le graphique.")
            
                with col2:
                                        # actual rank vs predicted rank charts
                    st.subheader("📊 Comparaison Positions Prédites vs Valeurs Prédites")
                    chart_data = result[['driver_code', 'team', 'PredictedRank', 'PredictedPositionValue', 'ActualPosition']].copy()
                    chart_data = chart_data.dropna(subset=['ActualPosition', 'PredictedRank']).drop(columns=['ActualPosition'])
                    
                    if not chart_data.empty:
                        # Créer le graphique côte à côte
                        chart = (
                                alt.Chart(chart_data)
                                .mark_bar(opacity=0.7)
                                .encode(
                                    x=alt.X('driver_code:N', title='Pilote', axis=alt.Axis(labelAngle=-45), 
                                    sort=alt.SortField(field='PredictedRank', order='ascending')),
                                    y=alt.Y('value:Q', title='Position', scale=alt.Scale(reverse=True)),
                                    color=alt.Color('variable:N',
                                                title='Type de Position',
                                                scale=alt.Scale(domain=['PredictedRank', 'PredictedPositionValue'],
                                                                range=['#1f77b4', '#e10600'])),
                                    xOffset=alt.XOffset('variable:N'),  # This creates the grouped bars
                                    tooltip=['driver_code', 'team', 'PredictedRank', 'PredictedPositionValue']
                                )
                                .transform_fold(
                                    ['PredictedRank', 'PredictedPositionValue'],
                                    as_=['variable', 'value']
                                )
                                .properties(
                                    width=400,  # Adjust overall width
                                    height=400,
                                    title=f'{selected_race} 2025'
                                )
                                .resolve_scale(
                                    color='independent'
                                )
                            )

                        st.altair_chart(chart, use_container_width=True)
                        
                        # Légende explicative
                        st.markdown("""
                        **Légende :**
                        - 🔴 **Rouge** : Position réelle
                        - 🔵 **Bleu** : Valeur prédite
                        - Plus la barre est haute, meilleure est la position (1 = 1er, 20 = 20ème)
                        """)
                    else:
                        st.warning("Aucune donnée de position réelle disponible pour créer le graphique.")
                
        else:
            st.warning("Aucune donnée pour la saison 2025 trouvée dans le fichier principal.")
