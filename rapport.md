# WEM : Web Mining - Laboratoire n°1 : Rapport

**Groupe:** Cyril Telley et Altin Hajda

**Date:** 13.03.2025

## 1. Introduction

Ce rapport décrit l'implémentation d'un crawler web, d'un système d'indexation avec Elasticsearch, et d'une fonction de recherche, dans le cadre du laboratoire n°1 du cours WEM.

## 2. Crawler (Scrapy)

### 2.1. Choix du Site Web

Nous avons choisi de crawler la version française de Wikipédia (`fr.wikipedia.org`). Ce choix a été motivé par :

- **Richesse du contenu:** Wikipédia offre une grande variété d'articles sur des sujets divers.
- **Données structurées:** Wikipédia utilise la norme Schema.org (via JSON-LD) pour fournir des métadonnées structurées, ce qui facilite l'extraction d'informations pertinentes.

- **Fichier `robots.txt`:** Wikipédia dispose d'un fichier `robots.txt` clair, permettant de crawler le site de manière responsable.

- **Structure HTML :** Difficulées avec wikipédia, les pages HTML ne sont pas stables

### 2.2. Éléments Indexés et Extraction

Nous avons décidé d'indexer les éléments suivants pour chaque page Wikipédia :

- **`url` (type: `keyword`):** L'URL complète de la page.
- **`titre` (type: `text`, analyzer: `french`):** Le titre principal de l'article (balise `<h1>`).
- **`resume` (type: `text`, analyzer: `french`):** Le premier paragraphe de l'article, servant de résumé.
- **`contenu` (type: `text`, analyzer: `french`):** Le contenu principal de l'article, nettoyé des balises HTML et autres éléments non pertinents.
- **`og_title` (type: `text`, analyzer: `french`):** Le titre Open Graph 
- **`og_description` (type: `text`, analyzer: `french`):** La description Open Graph.
- **`og_image` (type: `keyword`):** L'URL de l'image Open Graph.
- **`structured_data` (type: `object`):** Les données structurées (Schema.org) au format JSON-LD, avec les sous-champs:
  - `name` (type: `text`, analyzer: `french`)
  - `description` (type: `text`, analyzer: `french`)
  - `datePublished` (type: `date`, format: spécifié)
  - `author` (type: `object`)

**Méthodes d'Extraction:**

- **Sélecteurs CSS et XPath:** Nous avons utilisé les sélecteurs CSS et XPath de Scrapy pour cibler les éléments HTML contenant les informations voulues. Exemple, `response.css('h1#firstHeading').xpath('string(.)').get()` extrait le titre, et `response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()` gère les redirections.
- **BeautifulSoup:** Nous avons utilisé BeautifulSoup pour nettoyer le contenu HTML brut et pour extraire le résum. Exemple, `soup.find('p')` trouve le premier paragraphe, et `element.decompose()` supprime les éléments indésirables (tableaux, bandeaux, etc.). `stripped_strings` est utilisé pour obtenir un texte propre.
- **JSON-LD:** Nous avons extrait les données structurées en recherchant les balises `<script type="application/ld+json">` et en utilisant la librairie `json` de Python pour parser le contenu JSON.
- **Gestion des redirections**: La méthode `parse_item` commence par vérifier et gèrer les redirections internes de Wikipédia, grace à `response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()`.
- **Nettoyage**: Utilisation de `re.sub` pour le nettoyage du texte.

### 3 Recherche

### 3.1. Programme de Recherche (`search.py`)

Nous avons créé un programme Python indépendant (`search.py`) pour interroger l'index Elasticsearch. Ce programme :

1.  **Demande à l'utilisateur d'entrer une requête:**  Utilise la fonction `input()` pour récupérer le texte à rechercher.
2.  **Construit la requête Elasticsearch:**  Crée un dictionnaire Python représentant la requête au format JSON, qui est ensuite passé à Elasticsearch.
3.  **Exécute la requête:**  Utilise la méthode `es.search()` du client Python Elasticsearch pour envoyer la requête à Elasticsearch.
4.  **Traite les résultats:**  Extrait les informations pertinentes des résultats renvoyés par Elasticsearch (nombre total de résultats, score, titre, URL, résumé).
5.  **Affiche les résultats:**  Affiche les résultats à l'utilisateur dans la console, de manière formatée.
6.  **Gère la pagination:** Permet à l'utilisateur d'afficher les résultats page par page (10 résultats par page, configurable).
7.  **Ferme la connection:** Ferme la connection au serveur Elasticsearch

### 3.2. Requête Elasticsearch 

Le cœur de notre moteur de recherche est la requête Elasticsearch. Voici la requête que nous avons utilisée :

```python
query = {
    "query": {
        "bool": {
            "should": [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["titre^10", "og_title^8", "structured_data.name^7", "resume^5", "structured_data.description^4", "og_description^3", "contenu"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                {
                    "term": {
                        "url": {
                            "value": query_text,
                            "boost": 20
                        }
                    }
                }
            ]
        }
    },
    "from": from_result,
    "size": size
}
```

### 3.3.Recherche dans des Champs Spécifiques et Boosting


Elasticsearch offre plusieurs méthodes pour cibler des champs spécifiques lors d'une recherche. Les plus courantes sont :

1.  **Requête `match` (un seul champ):**

    Utilisez la requête `match` et spécifiez le nom du champ :

    ```json
    {
      "query": {
        "match": {
          "titre": {  // Recherche uniquement dans le champ "titre"
            "query": "texte recherché"
          }
        }
      }
    }
    ```

2.  **Requête `multi_match` (plusieurs champs):**

    Utilisez la requête `multi_match` et spécifiez la liste des champs dans le paramètre `fields` :

    ```json
    {
      "query": {
        "multi_match": {
          "query": "texte recherché",
          "fields": ["titre", "resume"]  // Recherche dans "titre" et "resume"
        }
      }
    }
    ```

3. **Requête `query_string`:**

   La requête `query_string` permet une syntaxe plus avancée, mais elle reste simple d'utilisation pour cibler des champs:

    ```json
   {
     "query": {
       "query_string": {
         "query": "titre:Paris AND contenu:France"
       }
     }
   }
    ```
  4. **Requête booléenne**
  Permet de combiner plusieurs requêtes.

**Comment "booster" certains champs ?**

Le "boosting" permet d'attribuer une importance plus grande à certains champs par rapport à d'autres.  Les documents correspondant dans un champ avec un boost élevé auront un score de pertinence plus élevé.

1.  **`multi_match` (Méthode Principale):**

    Dans une requête `multi_match`, ajoutez `^` suivi d'un nombre après le nom du champ :

    ```json
    {
      "query": {
        "multi_match": {
          "query": "texte recherché",
          "fields": ["titre^5", "resume^2", "contenu"] // "titre" est 5 fois plus important, "resume" 2 fois
        }
      }
    }
    ```
    Dans cet exemple, une correspondance dans le champ `titre` aura 5 fois plus de poids qu'une correspondance dans le champ `contenu` (qui a un boost implicite de 1). Le champ `resume` a, quant à lui, un boost de 2.

2.  **Requête `term` (Boost sur une clause spécifique):**

    Vous pouvez ajouter un paramètre `"boost"` à une clause `term` (utile pour les recherches exactes) :
     ```json
    {
        "query":{
            "term": {
                "url": {
                    "value": "[https://fr.wikipedia.org/wiki/France](https://fr.wikipedia.org/wiki/France)",
                    "boost": 20
                }
            }
        }
    }
     ```

3. **Requête `bool` (Boosting de Clauses):**
   Dans une requête booléenne, on peut attribuer un boost aux différentes clauses.
    ```json
   {
    "query":{
       "bool":{
          "must":[
             {"match": {"titre": {"query": "exemple", "boost": 4}}},
             {"match": {"resume":{"query": "exemple", "boost": 2}}}
           ]
        }
     }
   }
    ```
### 2.4 Questions théoriques

#### 2.4.1 Indexation multilingue

Pour indexer des pages dans plusieurs langues, il est essentiel d’adopter une stratégie efficace qui prend en compte les spécificités linguistiques de chaque langue. Voici quelques approches possibles :

1. **Indexation séparée par langue** :

   - Chaque langue possède son propre index Elasticsearch.
   - Avantages :
     - Meilleure pertinence des recherches en utilisant un analyseur linguistique adapté à chaque langue.
     - Facilité de gestion des spécificités linguistiques (stopwords, stemming, tokenisation).
   - Inconvénients :
     - Plus de ressources nécessaires (multiplication des index).
     - Complexité accrue dans la gestion des requêtes multi-langues.

2. **Indexation unique avec un champ de langue** :

   - Un seul index avec un champ indiquant la langue du document.
   - Utilisation de l’option `language` d’Elasticsearch pour appliquer un analyseur différent selon la langue.
   - Avantages :
     - Recherche centralisée, évitant la duplication des données.
     - Moins d’index à gérer, simplifiant l’architecture.
   - Inconvénients :
     - Risque de bruit linguistique (mélange d’algorithmes de recherche sur un même index).
     - Performance potentiellement dégradée.

3. **Indexation avec analyseurs multi-langues** :
   - Utilisation de l’analyseur `multi-fields` d’Elasticsearch permettant d’indexer un même champ avec plusieurs analyseurs linguistiques.
   - Avantages :
     - Recherche plus flexible et adaptable à plusieurs langues.
   - Inconvénients :
     - Impact sur l’espace de stockage et la performance.

En combinant ces méthodes, on améliore la pertinence et la performance de la recherche.

#### 2.4.2 Recherche floue (Fuzzy Query) et gestion des variations orthographiques

Elasticsearch permet d’effectuer des recherches floues grâce à l’algorithme de distance de Levenshtein, qui mesure le nombre d’opérations nécessaires pour transformer un mot en un autre (insertion, suppression, remplacement).

**Avantages de la recherche floue :**

- Permet de gérer les fautes de frappe et les variations mineures.
- Améliore la robustesse des recherches.

**Limitations pour les prénoms avec forte variabilité :**

- La recherche floue standard fonctionne bien pour des variations légères, mais elle peut être inefficace pour des noms avec de nombreuses variantes orthographiques comme _Caitlin_ (Caitlyn, Katelyn, Kaitlin, etc.).
- Trop de flexibilité peut conduire à des résultats non pertinents.

**Alternatives :**

1. **Dictionnaire de synonymes personnalisé** :

   - Création d’un fichier de synonymes (`synonym.txt`) utilisé dans l’analyseur Elasticsearch.
   - Exemple :
     ```
     Caitlin, Caitlyn, Katelyn, Kaitlin, Kaitlyn => Caitlin
     ```
   - Avantage : meilleure précision.

2. **N-grammes et phonétique** :
   - Utilisation des tokens N-grams ou des filtres phonétiques (Soundex, Metaphone) pour capturer des variations similaires.
   - Exemples :
     - `Caitlyn` et `Kaitlyn` peuvent être rapprochés via des algorithmes phonétiques.

En combinant ces approches, on optimise la recherche pour traiter efficacement les variations orthographiques tout en maintenant une bonne performance.
