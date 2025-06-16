# settings.py - Configuration complète pour FFVB Players Scraper
BOT_NAME = 'ffvb_scraper'

SPIDER_MODULES = ['ffvb_scraper.spiders']
NEWSPIDER_MODULE = 'ffvb_scraper.spiders'

# Obéir au robots.txt
ROBOTSTXT_OBEY = True

# Configuration des délais et concurrence
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# AutoThrottle pour ajustement automatique du débit
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True

# User-Agent par défaut (sera overridé par le middleware)
USER_AGENT = 'ffvb_scraper (+http://educational-purpose.local)'

# En-têtes par défaut
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# Configuration des middlewares
DOWNLOADER_MIDDLEWARES = {
    # Middlewares par défaut de Scrapy (désactivés si besoin)
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    
    # Nos middlewares personnalisés
    'ffvb_scraper.middlewares.RotateUserAgentMiddleware': 400,
    'ffvb_scraper.middlewares.HeadersMiddleware': 500,
    'ffvb_scraper.middlewares.CustomRetryMiddleware': 550,
    'ffvb_scraper.middlewares.ThrottleMiddleware': 600,
    'ffvb_scraper.middlewares.LoggingMiddleware': 650,
    'ffvb_scraper.middlewares.ResponseSizeMiddleware': 700,
    'ffvb_scraper.middlewares.ErrorHandlingMiddleware': 750,
    'ffvb_scraper.middlewares.CacheMiddleware': 800,
}

# Configuration des spider middlewares
SPIDER_MIDDLEWARES = {
    'ffvb_scraper.middlewares.FFVBScraperSpiderMiddleware': 543,
}

# Configuration des pipelines
ITEM_PIPELINES = {
    'ffvb_scraper.pipelines.ValidationPipeline': 200,
    'ffvb_scraper.pipelines.DuplicateFilterPipeline': 300,
    'ffvb_scraper.pipelines.CSVExportPipeline': 400,
    'ffvb_scraper.pipelines.JSONExportPipeline': 500,
    'ffvb_scraper.pipelines.DatabasePipeline': 600,
    'ffvb_scraper.pipelines.StatisticsPipeline': 700,
}

# Configuration des retry
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 400, 403]
RETRY_BACKOFF_BASE = 2.0
RETRY_BACKOFF_MAX = 60.0

# Configuration du cache (pour développement)
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = [404, 500, 502, 503, 504]

# Configuration des cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Configuration du logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'ffvb_scraper.log'
LOG_ENCODING = 'utf-8'

# Statistiques
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy.extensions.corestats.CoreStats': 500,
    'scrapy.extensions.memusage.MemoryUsage': 200,
}

# Configuration mémoire
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# Timeout des requêtes
DOWNLOAD_TIMEOUT = 30

# Configuration des redirections
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5

# Configuration des cookies par domaine
COOKIES_PER_DOMAIN_LIMIT = 16

# Configuration de compression
COMPRESSION_ENABLED = True

# Configuration DNS
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# Configuration des feeds (exports automatiques)
FEEDS = {
    'exports/players_%(name)s_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'item_classes': ['ffvb_scraper.items.PlayerItem'],
        'fields': [
            'nom', 'prenom', 'nom_complet', 'numero_maillot', 'poste',
            'taille', 'poids', 'age', 'club_actuel', 'equipe', 'url_source'
        ],
        'indent': 2,
    },
    'exports/teams_%(name)s_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'item_classes': ['ffvb_scraper.items.TeamItem'],
        'fields': ['nom_equipe', 'categorie', 'entraineur', 'url_source'],
    },
}

# Configuration Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# Configuration pour éviter les warnings
FEED_EXPORT_ENCODING = 'utf-8'

# Configuration personnalisée pour le projet FFVB
FFVB_SETTINGS = {
    'MAX_PLAYERS_PER_TEAM': 20,
    'ENABLE_PLAYER_PHOTOS': True,
    'VALIDATE_JERSEY_NUMBERS': True,
    'EXTRACT_DETAILED_STATS': False,  # Pour éviter de surcharger le site
    'SAVE_RAW_HTML': False,
    'TEAMS_TO_SCRAPE': [
        'Équipe de France Masculine',
        'Équipe de France Féminine',
        'Beach Volley France',
        'Équipes Jeunes'
    ]
}

# Configuration avancée pour la production
PRODUCTION_MODE = False  # Mettre à True pour la production
if PRODUCTION_MODE:
    LOG_LEVEL = 'WARNING'
    DOWNLOAD_DELAY = 5
    RANDOMIZE_DOWNLOAD_DELAY = 1.0
    AUTOTHROTTLE_START_DELAY = 3
    AUTOTHROTTLE_MAX_DELAY = 20
    HTTPCACHE_ENABLED = False
    CONCURRENT_REQUESTS = 1
    
# Configuration pour le développement
DEVELOPMENT_MODE = True
if DEVELOPMENT_MODE:
    # Logs plus détaillés en développement
    LOG_LEVEL = 'DEBUG'
    DOWNLOAD_DELAY = 1
    RANDOMIZE_DOWNLOAD_DELAY = 0.2
    # Cache activé pour développement plus rapide
    HTTPCACHE_ENABLED = True
    HTTPCACHE_EXPIRATION_SECS = 0  # Pas d'expiration en dev
    HTTPCACHE_DIR = 'httpcache'

# Configuration spécifique aux items
ITEM_PROCESSORS = {
    'PlayerItem': {
        'required_fields': ['nom_complet', 'equipe'],
        'optional_fields': ['poste', 'taille', 'numero_maillot', 'club_actuel'],
        'validate_jersey_numbers': True,
        'validate_height_range': (150, 220),  # cm
        'validate_weight_range': (50, 150),   # kg
    },
    'TeamItem': {
        'required_fields': ['nom_equipe'],
        'optional_fields': ['entraineur', 'categorie'],
    },
    'StaffItem': {
        'required_fields': ['fonction'],
        'optional_fields': ['nom', 'prenom'],
    }
}

# URLs et patterns spécifiques FFVB
FFVB_URL_PATTERNS = {
    'base_url': 'http://www.ffvb.org',
    'players_urls': [
        '/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0',  # URL principale
        '/384-37-1-Le-collectif',  # Équipe masculine
        '/386-37-1-Le-Collectif',  # Équipe féminine
    ],
    'teams_urls': [
        '/288-37-1-EQUIPES-DE-FRANCE',
        '/117-37-1-VOLLEY-BALL',
        '/282-37-1-BEACH-VOLLEY',
    ]
}

# Configuration des exports de données
DATA_EXPORT_CONFIG = {
    'csv_delimiter': ',',
    'csv_quotechar': '"',
    'json_indent': 2,
    'json_ensure_ascii': False,
    'sqlite_timeout': 30,
    'export_photos': True,
    'photos_directory': 'photos/',
    'max_file_size_mb': 100,
}

# Configuration du monitoring et des alertes
MONITORING_CONFIG = {
    'enable_performance_monitoring': True,
    'log_slow_requests': True,
    'slow_request_threshold': 10.0,  # secondes
    'enable_memory_monitoring': True,
    'memory_warning_threshold': 1024,  # MB
    'enable_error_reporting': True,
    'max_consecutive_errors': 5,
}

# Configuration de sécurité
SECURITY_CONFIG = {
    'respect_robots_txt': True,
    'max_requests_per_domain': 1000,
    'request_rate_limit': 60,  # requêtes par minute
    'enable_request_fingerprinting': True,
    'obfuscate_user_data': True,
}

# Validation finale des settings
def validate_settings():
    """Valider la cohérence des settings"""
    if DOWNLOAD_DELAY < 1 and PRODUCTION_MODE:
        raise ValueError("DOWNLOAD_DELAY doit être >= 1 en production")
    
    if not ROBOTSTXT_OBEY:
        import warnings
        warnings.warn("robots.txt ignoré - Vérifiez que c'est intentionnel")

# Appeler la validation au chargement
try:
    validate_settings()
except Exception as e:
    import logging
    logging.warning(f"Validation des settings: {e}")

# Configuration finale pour l'environnement
SCRAPY_PROJECT_NAME = 'ffvb_scraper'
SCRAPY_PROJECT_VERSION = '1.0.0'
SCRAPY_PROJECT_DESCRIPTION = 'Scraper professionnel pour les données FFVB'

# Messages de démarrage
STARTUP_MESSAGE = f"""
🏐 {SCRAPY_PROJECT_DESCRIPTION}
📦 Version: {SCRAPY_PROJECT_VERSION}
🔧 Mode: {'Production' if PRODUCTION_MODE else 'Développement'}
⏱️  Délai: {DOWNLOAD_DELAY}s
🤖 Robots.txt: {'Respecté' if ROBOTSTXT_OBEY else 'Ignoré'}
"""