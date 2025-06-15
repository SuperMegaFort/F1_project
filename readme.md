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

```
.
├── app/
│   ├── data/             # Données CSV utilisées par l'application
│   ├── models/           # Modèles ML entraînés
│   ├── pages/            # Les différentes pages de l'app Streamlit
│   ├── train_model/      # Scripts pour l'entraînement du modèle
│   ├── Home.py           # Page d'accueil de l'application
│   └── ...
├── doc/                  # Documentation du projet (rapport, etc.)
├── generate_dataset/
│   ├── circuit/          # Scripts pour scraper les données des circuits
│   ├── prediction/       # Scripts pour scraper les résultats des courses
│   └── team/             # Scripts pour scraper les données des pilotes
└── requirements.txt      # Dépendances du projet
```

---

## ⚙️ Installation et Utilisation

### 1. Prérequis

-   Python 3.9 ou supérieur
-   Un gestionnaire de paquets comme `pip`
-   Git

### 2. Installation

Clonez le dépôt et installez les dépendances :

```bash
# Clonez ce dépôt
git clone [https://github.com/VOTRE-NOM/VOTRE-REPO.git](https://github.com/VOTRE-NOM/VOTRE-REPO.git)

# Naviguez dans le dossier du projet
cd VOTRE-REPO

# Créez un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`

# Installez les dépendances
pip install -r requirements.txt
```

### 3. Collecte et Traitement des Données

Le processus se déroule en plusieurs étapes : scraping, première fusion, puis fusion finale.

#### a. Scraping des données brutes

Les scripts de scraping doivent être exécutés depuis le dossier `app/data` pour que les fichiers CSV y soient directement sauvegardés.

> **Note Importante pour `crawler_prediction.py`:**
> Ce script est paramétré pour scraper une plage d'années. Vous devez modifier la variable correspondante dans le script avant de l'exécuter :
> -   **Pour générer les données d'entraînement :** configurez la plage d'années de `2019` à `2024`.
> -   **Pour générer les données de test/prédiction :** configurez l'année sur `2025` uniquement.

```bash
# Naviguez vers le dossier cible
cd app/data

# Exemple pour exécuter le crawler des résultats de course
# (N'oubliez pas de configurer les années dans le script avant de lancer)
python ../../generate_dataset/prediction/crawler_prediction.py

# Répétez pour les autres crawlers (circuits, pilotes)
python ../../generate_dataset/circuit/crawler_circuit_v2.py
python ../../generate_dataset/team/crawler_pilote_v2.py
```

#### b. Fusion des données

Après avoir exécuté les crawlers, les scripts de fusion doivent être lancés **depuis la racine du projet**.

```bash
# Depuis la racine du projet, lancez la première fusion
python generate_dataset/prediction/merge_scraper.py

# Ensuite, lancez la fusion finale pour créer le jeu de données complet
python generate_dataset/prediction/merge_all_data.py
```

### 4. Entraînement du Modèle

Pour entraîner (ou ré-entraîner) le modèle de prédiction :

```bash
# Depuis la racine du projet
python app/train_model/model_training.py
```

Le modèle entraîné sera sauvegardé dans le dossier `app/models/`.

### 5. Lancement de l'Application Web

Une fois les données collectées et le modèle entraîné, lancez l'application Streamlit :

```bash
# Depuis la racine du projet
streamlit run app/Home.py
```

Ouvrez votre navigateur et allez à l'URL locale affichée (généralement `http://localhost:8501`).

---

## 👥 Contributeurs

-   **Cyril Telley** - *Collecte des données & Modélisation*
-   **Altin Hajda** - *Développement Web (Streamlit) & Modélisation*
-   **Hadil Zenati** - *Visualisation des données & UI/UX*
