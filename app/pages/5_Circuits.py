# pages/3_Circuits.py

import streamlit as st
import pandas as pd
import os

# --- Configuration de la Page ---
st.set_page_config(
    layout="wide",
    page_title="Infos Circuits F1",
    page_icon="🌍"
)

st.title("🌍 Explorez les Circuits de Formule 1")
st.markdown("---")

# --- Chargement des données (avec mise en cache pour la performance) ---
@st.cache_data
def load_circuits_data():
    """Charge les données des circuits depuis le fichier CSV."""
    file_path = 'data/circuits_data.csv'
    if not os.path.exists(file_path):
        st.error(f"Le fichier '{file_path}' est introuvable. Veuillez d'abord exécuter le script `extract_circuits_from_cache.py`.")
        return None
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture du fichier CSV : {e}")
        return None

# --- Application Principale ---
circuits_df = load_circuits_data()

if circuits_df is not None:
    # Trier les circuits par nom pour une sélection plus facile
    circuit_list = circuits_df['circuitName'].sort_values().tolist()
    
    # Créer une liste déroulante dans la barre latérale pour choisir un circuit
    with st.sidebar:
        st.header("Filtres")
        selected_circuit_name = st.selectbox(
            'Choisissez un circuit :',
            circuit_list
        )

    # Récupérer la ligne de données pour le circuit sélectionné
    circuit_data = circuits_df[circuits_df['circuitName'] == selected_circuit_name].iloc[0]

    # --- Affichage des informations détaillées ---
    st.header(f"📍 {circuit_data['circuitName']}")
    
    # Organiser l'affichage en deux colonnes
    col1, col2 = st.columns([2, 1]) # 2/3 de la largeur pour l'image, 1/3 pour les métriques

    with col1:
        # Afficher l'image du tracé du circuit
        st.image(
            circuit_data['imageUrl'],
            caption=f"Tracé du circuit {circuit_data['circuitName']}"
        )

    with col2:
        # Afficher les informations clés avec st.metric pour un look propre
        st.metric("Pays", circuit_data['country'])
        st.metric("Ville / Région", circuit_data['locality'])
        st.metric("Longueur du Circuit", f"{circuit_data['circuitLengthKm']:.3f} km")
        st.metric("Nombre de Virages", f"{int(circuit_data['corners'])}")
        
        st.markdown("---")
        st.subheader("Meilleur Tour en Course")
        st.metric("Pilote", circuit_data['bestLapDriver'])
        st.metric("Temps", circuit_data['bestLapTimeStr'])
        st.caption(f"Données de la saison {circuit_data['sourceYear']}")
else:
    st.info("En attente du chargement des données des circuits...")