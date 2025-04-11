BOT_NAME = "F1_project"

SPIDER_MODULES = ["F1_project.spiders"]
NEWSPIDER_MODULE = "F1_project.spiders"

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
    'F1_project.pipelines.ElasticsearchPipeline': 300,
}

SPLASH_URL = 'http://localhost:8050'

DOWNLOADER_MIDDLEWARES = {
    'F1_project.middlewares.HandleOffsiteMiddleware': 542,  # Correct placement
    'scrapy.downloadermiddlewares.offsite.OffsiteMiddleware': 543, # Must be AFTER
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
}

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

ELASTICSEARCH_SERVER = 'http://localhost:9200'
ELASTICSEARCH_INDEX = 'f1_index'

DOWNLOAD_DELAY = 1
CLOSESPIDER_PAGECOUNT = 100
DEPTH_LIMIT = 5

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"