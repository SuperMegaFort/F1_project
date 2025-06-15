# pages/4_Circuits_Details.py (ou le nom que vous souhaitez)

import streamlit as st
import pandas as pd
import os

# --- Configuration de la Page ---
st.set_page_config(
    layout="wide",
    page_title="Détails des Circuits F1",
    page_icon="🌍"
)

st.title("🌍 Explorez les Circuits du Championnat")
st.markdown("Retrouvez les informations clés et les records pour chaque circuit de la saison.")
st.markdown("---")

# --- Configuration des chemins ---
# Adaptez ce chemin si votre CSV est dans un autre dossier
# Le nom du fichier inclut l'année, pensez à l'adapter si nécessaire
YEAR_TO_DISPLAY = 2024
CIRCUITS_DATA_PATH = os.path.join("data", f"f1_circuits_{YEAR_TO_DISPLAY}.csv")

# --- Fonction de chargement des données (avec cache) ---
@st.cache_data(ttl="6h")
def load_circuits_data(path):
    """Charge les données des circuits depuis le fichier CSV généré par le scraper."""
    if not os.path.exists(path):
        st.error(f"Le fichier de données des circuits '{path}' est introuvable.")
        st.warning("Veuillez d'abord exécuter le script `crawler_circuits.py` pour générer ce fichier.")
        return None
    
    try:
        df = pd.read_csv(path)
        # Nettoyage des données pour un affichage propre
        df.fillna({
            'length_km': 0,
            'laps': 0,
            'lap_record_time': 'N/A',
            'lap_record_driver': 'N/A',
            'first_gp': 'N/A',
            'image_url': '',
            'country_flag_url': ''
        }, inplace=True)
        return df
    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture du fichier CSV : {e}")
        return None

# --- Application Principale ---
circuits_df = load_circuits_data(CIRCUITS_DATA_PATH)

if circuits_df is not None and not circuits_df.empty:
    
    # Trier les circuits par leur nom pour un affichage alphabétique
    circuits_df.sort_values('circuit_name', inplace=True)

    # Définir le nombre de colonnes pour la galerie
    cols = st.columns(2)
    
    # Itérer sur les données pour créer une carte par circuit
    for index, circuit in circuits_df.iterrows():
        col = cols[index % 2] # Assigner la carte à une colonne (gauche/droite)

        with col:
            with st.container(border=True):
                # Header de la carte avec le drapeau et le nom
                col1, col2 = st.columns([1, 4])
                with col1:
                    if circuit['country_flag_url']:
                        st.image(circuit['country_flag_url'], width=60)
                with col2:
                    st.subheader(circuit['circuit_name'])

                # Tracé du circuit
                if circuit['image_url']:
                    st.image(circuit['image_url'], use_container_width=True)
                else:
                    st.image("https://placehold.co/600x400/F0F2F6/E10600?text=Tracé\\nIndisponible", use_container_width=True)

                st.markdown("---")

                # Affichage des statistiques principales avec st.metric
                m_cols = st.columns(3)
                m_cols[0].metric("Longueur", f"{circuit.get('length_km', 0)} km")
                m_cols[1].metric("Tours", f"{int(circuit.get('laps', 0))}")
                m_cols[2].metric("Premier GP", str(circuit.get('first_gp', 'N/A')))
                
                # Expander pour le record du tour
                with st.expander("Record du Tour"):
                    st.metric("Temps Record", str(circuit.get('lap_record_time', 'N/A')))
                    st.caption(f"Par : {circuit.get('lap_record_driver', 'N/A')}")

else:
    st.info("En attente des données des circuits. Le fichier CSV est peut-être en cours de création.")

# Pied de page
st.markdown("---")
st.caption("Données collectées via le scraper de circuits personnalisé.")
