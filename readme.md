# Projet d'Analyse et de Prédiction de Données de Formule 1

Ce projet, réalisé dans le cadre d'un Master en Data Science, vise à construire un pipeline complet pour l'analyse et la prédiction des résultats de courses de Formule 1. Il inclut la collecte de données par web scraping, leur traitement, l'entraînement d'un modèle de Machine Learning et la visualisation des résultats via une application web interactive.

![Aperçu de l'application Streamlit](https://placehold.co/800x450/2d3748/ffffff?text=Aperçu+de+l'application+Streamlit)
*Un aperçu de l'interface principale de l'application Streamlit.*

---

## 🚀 Fonctionnalités

L'application web, développée avec **Streamlit**, offre plusieurs modules :

-   **Dashboard Interactif :** Visualisez les classements, la progression des points et la distribution des résultats pour les pilotes et les écuries.
-   **Exploration des Données :** Naviguez et filtrez les résultats de toutes les sessions (Essais Libres, Qualifications, Course) pour les saisons de 2018 à 2024.
-   **Prédiction par Machine Learning :** Obtenez le classement de course prédit pour n'importe quel Grand Prix de l'historique grâce à un modèle LightGBM.
-   **Encyclopédie F1 :** Consultez des fiches détaillées sur les pilotes, les écuries et les circuits du championnat.

---

## 🛠️ Tech Stack

-   **Langage :** Python 3.9+
-   **Collecte de Données :**
    -   `Requests` pour les requêtes HTTP.
    -   `BeautifulSoup4` & `Selenium` pour le web scraping.
-   **Analyse de Données :**
    -   `Pandas` pour la manipulation et le traitement des données.
    -   `NumPy` pour les opérations numériques.
-   **Machine Learning :**
    -   `Scikit-learn` pour le pipeline de modélisation.
    -   `LightGBM` comme algorithme de prédiction principal.
-   **Application Web :**
    -   `Streamlit` pour la création de l'interface utilisateur.
    -   `Plotly` pour les visualisations de données interactives.

---

## 📂 Structure du Projet
