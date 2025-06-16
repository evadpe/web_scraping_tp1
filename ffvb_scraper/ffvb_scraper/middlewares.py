# middlewares.py
import random
import time
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from itemadapter import is_item, ItemAdapter
import logging

class RotateUserAgentMiddleware:
    """Middleware pour faire tourner les User-Agents"""
    
    def __init__(self):
        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
    
    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        spider.logger.debug(f"User-Agent utilisé: {ua}")

class CustomRetryMiddleware(RetryMiddleware):
    """Middleware de retry personnalisé avec backoff exponentiel"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.backoff_base = settings.getfloat('RETRY_BACKOFF_BASE', 2.0)
        self.backoff_max = settings.getfloat('RETRY_BACKOFF_MAX', 60.0)
    
    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            
            # Calculer le délai avec backoff exponentiel
            retry_times = request.meta.get('retry_times', 0) + 1
            delay = min(self.backoff_base ** retry_times, self.backoff_max)
            
            spider.logger.warning(f"Retry {retry_times} pour {request.url} dans {delay:.1f}s - Raison: {reason}")
            
            # Attendre avant de retry
            time.sleep(delay)
            
            return self._retry(request, reason, spider) or response
        
        return response

class HeadersMiddleware:
    """Middleware pour ajouter des en-têtes HTTP personnalisés"""
    
    def process_request(self, request, spider):
        # En-têtes pour simuler un navigateur réel
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Ajouter un referer si ce n'est pas la première requête
        if hasattr(spider, 'start_urls') and request.url not in spider.start_urls:
            request.headers['Referer'] = 'http://www.ffvb.org/'

class LoggingMiddleware:
    """Middleware pour logging détaillé"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.response_count = 0
        self.error_count = 0
    
    def process_request(self, request, spider):
        self.request_count += 1
        spider.logger.debug(f"📤 Requête #{self.request_count}: {request.url}")
    
    def process_response(self, request, response, spider):
        self.response_count += 1
        elapsed = time.time() - self.start_time
        
        spider.logger.debug(f"📥 Réponse #{self.response_count}: {response.status} - {request.url}")
        
        # Log périodique des statistiques
        if self.response_count % 10 == 0:
            spider.logger.info(f"📊 Stats: {self.response_count} réponses en {elapsed:.1f}s")
        
        return response
    
    def process_exception(self, request, exception, spider):
        self.error_count += 1
        spider.logger.error(f"❌ Erreur #{self.error_count}: {exception} - {request.url}")

class CacheMiddleware:
    """Middleware de cache simple pour éviter les requêtes redondantes"""
    
    def __init__(self):
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def process_request(self, request, spider):
        # Pour le développement, on peut activer le cache
        if hasattr(spider, 'use_cache') and spider.use_cache:
            if request.url in self.cache:
                self.cache_hits += 1
                spider.logger.debug(f"🎯 Cache hit: {request.url}")
                return HtmlResponse(
                    url=request.url,
                    body=self.cache[request.url],
                    encoding='utf-8'
                )
        return None
    
    def process_response(self, request, response, spider):
        # Mettre en cache les réponses réussies
        if hasattr(spider, 'use_cache') and spider.use_cache and response.status == 200:
            self.cache[request.url] = response.body
            self.cache_misses += 1
            spider.logger.debug(f"💾 Mise en cache: {request.url}")
        
        return response

class ThrottleMiddleware:
    """Middleware pour limiter le débit de requêtes par domaine"""
    
    def __init__(self):
        self.domain_delays = {}
        self.last_request_time = {}
    
    def process_request(self, request, spider):
        domain = request.url.split('/')[2]  # Extraire le domaine
        
        # Délai par défaut ou configuré
        delay = getattr(spider, 'custom_delay', 2.0)
        
        # Vérifier le délai depuis la dernière requête
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < delay:
                sleep_time = delay - elapsed
                spider.logger.debug(f"⏱️  Throttle: attendre {sleep_time:.1f}s pour {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()

class ResponseSizeMiddleware:
    """Middleware pour surveiller la taille des réponses"""
    
    def __init__(self):
        self.total_size = 0
        self.response_count = 0
    
    def process_response(self, request, response, spider):
        response_size = len(response.body)
        self.total_size += response_size
        self.response_count += 1
        
        # Log des réponses volumineuses
        if response_size > 1024 * 1024:  # > 1MB
            spider.logger.info(f"📦 Réponse volumineuse: {response_size/1024/1024:.1f}MB - {request.url}")
        
        # Stats périodiques
        if self.response_count % 20 == 0:
            avg_size = self.total_size / self.response_count
            spider.logger.info(f"📈 Taille moyenne des réponses: {avg_size/1024:.1f}KB")
        
        return response

class ErrorHandlingMiddleware:
    """Middleware pour gestion avancée des erreurs"""
    
    def __init__(self):
        self.error_stats = {}
    
    def process_exception(self, request, exception, spider):
        error_type = type(exception).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        spider.logger.error(f"🚫 {error_type}: {exception} - {request.url}")
        
        # Log des stats d'erreur périodiquement
        if sum(self.error_stats.values()) % 5 == 0:
            spider.logger.warning(f"📊 Erreurs: {dict(self.error_stats)}")
    
    def process_response(self, request, response, spider):
        # Traiter les codes d'erreur HTTP
        if response.status >= 400:
            error_code = f"HTTP_{response.status}"
            self.error_stats[error_code] = self.error_stats.get(error_code, 0) + 1
            
            if response.status == 404:
                spider.logger.warning(f"🔍 Page non trouvée: {request.url}")
            elif response.status == 403:
                spider.logger.warning(f"🚫 Accès interdit: {request.url}")
            elif response.status >= 500:
                spider.logger.error(f"🔥 Erreur serveur {response.status}: {request.url}")
        
        return response

class FFVBScraperSpiderMiddleware:
    """Middleware spécifique au spider FFVB"""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s
    
    def process_spider_input(self, response, spider):
        return None
    
    def process_spider_output(self, response, result, spider):
        # Traiter les résultats du spider
        for i in result:
            yield i
    
    def process_spider_exception(self, response, exception, spider):
        spider.logger.error(f"Exception dans le spider: {exception}")
    
    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r
    
    def spider_opened(self, spider):
        spider.logger.info(f'🕷️  Spider ouvert: {spider.name}')

def response_status_message(status):
    """Retourner un message pour un code de statut HTTP"""
    messages = {
        400: "Bad Request",
        401: "Unauthorized", 
        403: "Forbidden",
        404: "Not Found",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }
    return messages.get(status, f"HTTP {status}")