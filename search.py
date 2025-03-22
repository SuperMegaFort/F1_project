from elasticsearch import Elasticsearch

def rechercher(query_text, elastic_server='http://localhost:9200', elastic_index='f1_index', from_result=0, size=10):
    es = Elasticsearch(elastic_server)

    # Construction de la requête Elasticsearch
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
        "from": from_result,  # Gestion de la pagination (début)
        "size": size          # Gestion de la pagination (taille du lot)
    }

    # Exécution de la requête
    results = es.search(index=elastic_index, body=query)
    es.close() 
    return results 

if __name__ == "__main__":
    recherche_terme = input("Entrez votre recherche : ")
    
    page_size = 10  # Nombre de résultats par page
    page_num = 0    # Page actuelle (commence à 0)

    while True: # Boucle pour afficher les résultats par page
        results = rechercher(recherche_terme, from_result=page_num * page_size, size=page_size)
         # Traitement et affichage des résultats
        print(f"Nombre total de résultats : {results['hits']['total']['value']}")
        print(f"Résultats {page_num * page_size + 1} à {min((page_num + 1) * page_size, results['hits']['total']['value'])} :")

        for hit in results['hits']['hits']:
            print(f"\nScore: {hit['_score']}")
            print(f"Titre: {hit['_source'].get('titre', '')}")
            print(f"Date de publication: {hit['_source'].get('structured_data', {}).get('datePublished', '')}")
            print(f"URL: {hit['_source']['url']}")
            #print(f"Contenu: {hit['_source'].get('contenu', '')}") (ne fonctionne pas)
            #print(f"Résumé: {hit['_source'].get('resume', '')}")   (ne fonctionne pas)
            #print(f"Image: {hit['_source'].get('og_image', '')}")  (ne fonctionne pas)

            print(f"Description Open Graph: {hit['_source'].get('og_description', '')}")


        if (page_num + 1) * page_size >= results['hits']['total']['value'] : 
            break

        reponse = input("\nAfficher la page suivante ? (o/n) : ").lower()
        if reponse != 'o':
            break

        page_num += 1 