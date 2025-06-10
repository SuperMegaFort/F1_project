import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Accueil - Analyse F1",
    page_icon="🏎️" 
)

st.title("🏎️ Bienvenue sur l'Analyseur de Données de Formule 1")

st.markdown("""
Bienvenue sur cette application dédiée à l'exploration et à la visualisation des données de Formule 1 des saisons 2015 à 2024.

**Utilisez la navigation dans la barre latérale à gauche pour :**
* Explorer les **Données Générales (`Data Overview`)** sous forme de tableaux interactifs.
* Plonger dans les **Visualisations de Données (`Data Visualisation`)** pour analyser les performances des pilotes.

Nous espérons que cet outil vous sera utile pour vos analyses !
""")

st.sidebar.success("Navigation Principale")
st.sidebar.markdown("---")
st.sidebar.info("Sélectionnez une page ci-dessus pour commencer.")