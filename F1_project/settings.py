BOT_NAME = "F1_project"

SPIDER_MODULES = ["F1_project.spiders"]
NEWSPIDER_MODULE = "F1_project.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Active les pipelines (pour l'envoi vers Elasticsearch)
ITEM_PIPELINES = {
    'F1_project.pipelines.ElasticsearchPipeline': 300,
}

# Configuration de Splash
SPLASH_URL = 'http://localhost:8050'

DOWNLOADER_MIDDLEWARES = {
    # 'scrapy.downloadermiddlewares.offsite.OffsiteMiddleware',  # Keep commented out for initial test
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810, # UNcommented!
}

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'  # Optional: for caching

# Configuration d'Elasticsearch
ELASTICSEARCH_SERVER = 'http://localhost:9200'  # L'URL pour accéder à Elasticsearch
ELASTICSEARCH_INDEX = 'f1_index'  # Nom de l'index Elasticsearch

# Pour éviter le bannissement
DOWNLOAD_DELAY = 1  # Délai d'au moins 1 seconde entre les requêtes
#USER_AGENT = 'HEG-WebMining-Bot (ton_email@example.com)'  Ps obligatoire

# Limite le nombre de pages pour éviter un crawl infini
CLOSESPIDER_PAGECOUNT = 100
DEPTH_LIMIT = 5

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"