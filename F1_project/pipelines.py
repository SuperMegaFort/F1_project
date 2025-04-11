import logging
import elasticsearch

class ElasticsearchPipeline:

    def __init__(self, elastic_host, elastic_index):
        self.elastic_host = elastic_host
        self.elastic_index = elastic_index
        self.es = None  # Initialisation différée

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            elastic_host=crawler.settings.get('ELASTICSEARCH_SERVER'),
            elastic_index=crawler.settings.get('ELASTICSEARCH_INDEX')
        )

    def open_spider(self, spider):
        # Initialiser la connexion Elasticsearch ici
        self.es = elasticsearch.Elasticsearch(hosts=[self.elastic_host])
        if not self.es.indices.exists(index=self.elastic_index):
            self.es.indices.create(index=self.elastic_index)
            logging.info(f"Index Elasticsearch '{self.elastic_index}' créé.")
        else:
            logging.info(f"L'index Elasticsearch '{self.elastic_index}' existe déjà.")


    def close_spider(self, spider):
        # Aucune action nécessaire pour fermer la connexion avec le client Elasticsearch actuel
        pass

    def process_item(self, item, spider):
        try:
            self.es.index(index=self.elastic_index, document=item)
            logging.debug(f"Item ajouté à Elasticsearch: {item}") #Utiliser logging au lieu de print
        except elasticsearch.ElasticsearchException as e:
            logging.error(f"Erreur lors de l'ajout à Elasticsearch: {e}")
        return item