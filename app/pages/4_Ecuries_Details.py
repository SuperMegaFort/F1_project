# pages/3_Pilotes_Details.py

import streamlit as st
import pandas as pd
import os # Ajout pour la gestion des chemins de fichiers

# --- Configuration des chemins ---
# Adaptez ce chemin si votre fichier CSV est dans un autre dossier
DRIVERS_DATA_PATH = os.path.join("data", "f1_drivers_all.csv")

# --- Configuration de la Page ---
st.set_page_config(
    layout="wide",
    page_title="Détails des Pilotes F1",
    page_icon="🧑‍🚀" # Icône de pilote
)

st.title("🧑‍🚀 Galerie des Pilotes de Formule 1")
st.markdown("Explorez les informations détaillées sur chaque pilote, regroupées par écurie.")
st.markdown("---")

TEAM_COLORS = {
    'Mercedes': '#6CD3BF',
    'Ferrari': '#F91536',
    'Red Bull Racing': '#3671C6',
    'McLaren': '#F58020',
    'Aston Martin': '#358C75',
    'Alpine': '#2293D1',
    'Williams': '#64C4FF',
    'Racing Bulls': '#6692FF',
    'Kick Sauber': '#52E252',
    'Haas': '#B6BABD',
    'Default': '#333333'
}

TEAM_LOGOS = {
    'Mercedes': 'https://media.formula1.com/content/dam/fom-website/teams/2024/mercedes.png',
    'Ferrari': 'https://media.formula1.com/content/dam/fom-website/teams/2024/ferrari.png',
    'Red Bull Racing': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/red-bull-racing.png',
    'McLaren': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/mclaren.png',
    'Aston Martin': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/aston-martin.png',    
    'Alpine': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/alpine.png',
    'Williams': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/williams.png',
    'Racing Bulls': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/racing-bulls.png',
    'Kick Sauber': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/kick-sauber.png',
    'Haas': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2025/haas.png',
    'Default': ''
}


# --- Fonction de chargement des données (avec cache pour la performance) ---
@st.cache_data(ttl="6h")
def load_drivers_data(path):
    """Charge les données des pilotes depuis le fichier CSV."""
    try:
        df = pd.read_csv(path)
        # Nettoyage simple : Remplacer les N/A par des chaînes vides ou des zéros
        df.fillna({
            'team': 'Écurie Inconnue', # Donner un nom par défaut
            'country': 'N/A',
            'podiums': 0,
            'points': 0,
            'main_image_url': ''
        }, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Fichier des pilotes introuvable ! Assurez-vous que le chemin '{path}' est correct.")
        return None

# --- Chargement des données ---
drivers_df = load_drivers_data(DRIVERS_DATA_PATH)

if drivers_df is None:
    st.warning("Les données des pilotes n'ont pas pu être chargées. Le scraper a-t-il bien été exécuté ?")
    st.stop() # Arrête l'exécution si le fichier est introuvable


# --- Affichage principal regroupé par écurie ---
# Obtenir la liste unique des écuries et la trier
teams_list = sorted(drivers_df['team'].unique())

if not teams_list:
    st.info("Aucune écurie trouvée dans les données.")
else:
    for team in teams_list:
        logo_url = TEAM_LOGOS.get(team, TEAM_LOGOS['Default'])
        st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 15px; border-radius: 10px; margin-bottom: 25px;">
                <img src="{logo_url}" style="height: 75px; margin-right: 20px;"/>
                <h2 style="color: white; margin: 0; font-size: 40px">{team}</h2>
            </div>
        """, unsafe_allow_html=True)
        
        team_drivers_df = drivers_df[drivers_df['team'] == team].sort_values(by="full_name")
        
        cols = st.columns(3) 
        
        for i, (index, driver) in enumerate(team_drivers_df.iterrows()):
            col = cols[i % 3] 
            
            with col:
                with st.container(border=True):
                    ### NOUVEAU ###
                    # Récupérer la couleur de l'écurie
                    team_color = TEAM_COLORS.get(team, TEAM_COLORS['Default'])
                    
                    st.markdown(f'<div style="background-color:{team_color}; height: 10px; border-radius: 5px 5px 0 0; margin-top: -15px; margin-left: -15px; margin-right: -15px; margin-bottom: 15px;"></div>', unsafe_allow_html=True)

                    if pd.notna(driver['main_image_url']) and driver['main_image_url']:
                        st.image(
                            driver['main_image_url'], 
                            caption=f"{driver['full_name']}",
                            use_container_width=True
                        )
                    else:
                        st.image(
                            "https://placehold.co/400x300/F0F2F6/E10600?text=Image\\nNon\\nDisponible", 
                            caption=f"{driver['full_name']}",
                            use_container_width=True
                        )

                    st.subheader(f"{driver['full_name']} `#{driver['driver_number']}`")

                    m_cols = st.columns(2)
                    m_cols[0].metric(label="Pays", value=str(driver['country']))
                    m_cols[1].metric(label="Points", value=int(driver.get('points', 0)))
                    
                    with st.expander("Plus d'informations"):
                        st.markdown(f"**Date de naissance :** {driver.get('date_of_birth', 'N/A')}")
                        st.markdown(f"**Lieu de naissance :** {driver.get('place_of_birth', 'N/A')}")
                        st.markdown(f"**Podiums :** {int(driver.get('podiums', 0))}")
                        st.markdown(f"**Grands Prix disputés :** {driver.get('grands_prix_entered', 'N/A')}")
                        st.markdown(f"**Championnats du monde :** {driver.get('world_championships', 'N/A')}")
                        st.markdown(f"**Meilleur résultat en course :** {driver.get('highest_race_finish', 'N/A')}")
                        st.markdown(f"**Meilleure position sur la grille :** {driver.get('highest_grid_position', 'N/A')}")
        
        st.markdown("---")

# Pied de page
st.caption("Données collectées via le scraper personnalisé.")