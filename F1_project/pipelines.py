from elasticsearch import Elasticsearch, ApiError, NotFoundError, ConnectionError  
from itemadapter import ItemAdapter
from dateutil import parser  

class ElasticsearchPipeline:

    def __init__(self, elastic_server, elastic_index):
        self.elastic_server = elastic_server
        self.elastic_index = elastic_index
        self.es = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            elastic_server=crawler.settings.get('ELASTICSEARCH_SERVER'),
            elastic_index=crawler.settings.get('ELASTICSEARCH_INDEX', 'f1_index'),
        )

    def open_spider(self, spider):
        try:
            self.es = Elasticsearch(self.elastic_server)
            if not self.es.indices.exists(index=self.elastic_index):
                self.es.indices.create(
                    index=self.elastic_index,
                    body={
                        "mappings": {
                            "properties": {
                                "url": {"type": "keyword"},
                                "titre": {"type": "text", "analyzer": "french"},
                                "resume": {"type": "text", "analyzer": "french"},
                                "contenu": {"type": "text", "analyzer": "french"},
                                "og_title": {"type": "text", "analyzer": "french"},
                                "og_description": {"type": "text", "analyzer": "french"},
                                "og_image":{"type": "keyword"},
                                "structured_data": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "text", "analyzer": "french"},
                                        "description": {"type": "text", "analyzer": "french"},
                                        "datePublished": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd'T'HH:mm:ss.SSSZ||yyyy-MM-dd'T'HH:mm:ssZ||yyyy-MM-dd||epoch_millis"}, #Ajout du format
                                        "author": {
                                            "type": "object",
                                            "properties":{
                                                "name": {"type": "text", "analyzer": "french"},
                                                "url": {"type":"keyword"}
                                            }
                                        },
                                        "image": {"type": "keyword"},
                                    },
                                },
                            }
                        }
                    },
                )
        except ApiError as e:  # CORRIGÉ: Utilise ApiError
            print(f"ERREUR Elasticsearch (open_spider): {e}")
            spider.crawler.engine.close_spider(spider, 'elasticsearch_error') #Arrêt du crawler


    def close_spider(self, spider):
        if self.es:
          try:
            self.es.close()
          except ApiError as e:  # CORRIGÉ: Utilise ApiError
              print(f"ERREUR Elasticsearch (close_spider): {e}")

    def process_item(self, item, spider):
        if self.es:
            adapter = ItemAdapter(item)
            try:
                # Transformation de datePublished (
                if 'structured_data' in adapter and 'datePublished' in adapter['structured_data']:
                    date_str = adapter['structured_data']['datePublished']
                    parsed_date = parser.parse(date_str)  # Parse la date
                    adapter['structured_data']['datePublished'] = parsed_date.isoformat() # Convertit en ISO 8601
            except (ValueError, TypeError):
                pass

            try:
                self.es.index(index=self.elastic_index, document=adapter.asdict())
            except ApiError as e:  # CORRIGÉ: Utilise ApiError / sinon erreur
                print(f"ERREUR Elasticsearch (process_item): {e}")
                # Gérer l'erreur (logger, réessayer, etc.)

        return item