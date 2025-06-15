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
    # Boucler sur chaque écurie pour créer une section dédiée
    for team in teams_list:
        st.header(f"🏎️ {team}")
        
        # Filtrer les pilotes pour l'écurie actuelle
        team_drivers_df = drivers_df[drivers_df['team'] == team].sort_values(by="full_name")
        
        # Définir le nombre de colonnes pour la galerie
        cols = st.columns(3) 
        
        # CORRECTION : Utiliser enumerate pour obtenir un index stable (0, 1, 2...)
        # Cela garantit que les pilotes sont placés dans les colonnes dans le bon ordre.
        for i, (index, driver) in enumerate(team_drivers_df.iterrows()):
            # Placer chaque pilote dans une colonne en utilisant l'index de l'énumération
            col = cols[i % 3] 
            
            with col:
                # Conteneur pour un effet de "carte" avec une bordure
                with st.container(border=True):
                    
                    # Afficher l'image du pilote, avec une image de secours si l'URL est manquante
                    if pd.notna(driver['main_image_url']) and driver['main_image_url']:
                        st.image(
                            driver['main_image_url'], 
                            caption=f"{driver['full_name']}",
                            use_container_width=True
                        )
                    else:
                        # Image de secours
                        st.image(
                            "https://placehold.co/400x300/F0F2F6/E10600?text=Image\\nNon\\nDisponible", 
                            caption=f"{driver['full_name']}",
                            use_container_width=True
                        )

                    # Nom et numéro
                    st.subheader(f"{driver['full_name']} `#{driver['driver_number']}`")

                    # Statistiques clés avec st.metric pour un affichage impactant
                    m_cols = st.columns(2)
                    m_cols[0].metric(label="Pays", value=str(driver['country']))
                    m_cols[1].metric(label="Points", value=int(driver.get('points', 0)))
                    
                    # Expander pour les détails moins importants
                    with st.expander("Plus d'informations"):
                        st.markdown(f"**Date de naissance :** {driver.get('date_of_birth', 'N/A')}")
                        st.markdown(f"**Lieu de naissance :** {driver.get('place_of_birth', 'N/A')}")
                        st.markdown(f"**Podiums :** {int(driver.get('podiums', 0))}")
                        st.markdown(f"**Grands Prix disputés :** {driver.get('grands_prix_entered', 'N/A')}")
                        st.markdown(f"**Championnats du monde :** {driver.get('world_championships', 'N/A')}")
                        st.markdown(f"**Meilleur résultat en course :** {driver.get('highest_race_finish', 'N/A')}")
                        st.markdown(f"**Meilleure position sur la grille :** {driver.get('highest_grid_position', 'N/A')}")
        
        # Ajouter un séparateur entre chaque écurie
        st.markdown("---")

# Pied de page
st.caption("Données collectées via le scraper personnalisé.")
