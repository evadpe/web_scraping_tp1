# run_debug_simple.py
import sys
import os
from scrapy.crawler import CrawlerProcess

def run_debug_simple():
    """Lance le debug simple pour comprendre la structure de la page"""
    print("🔍 DEBUG SIMPLE - ANALYSE DE LA PAGE FFVB")
    print("=" * 50)
    print("🎯 Objectif: Analyser la structure de la page cible")
    print("📄 URL: http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0")
    print("📁 Fichiers générés:")
    print("   - ffvb_debug_output.csv (tout ce qui est trouvé)")
    print("   - debug_page_source.html (code source de la page)")
    print()
    
    # Ajouter au PYTHONPATH
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Configuration Scrapy minimale
    settings = {
        'BOT_NAME': 'ffvb_debug',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ITEM_PIPELINES': {},  # Pas de pipelines
        'DOWNLOADER_MIDDLEWARES': {},  # Pas de middlewares
    }
    
    process = CrawlerProcess(settings)
    
    try:
        from ffvb_scraper.spiders.ffvb_simple_debug_spider import FFVBSimpleDebugSpider
        
        print("🕷️  Démarrage du debug...")
        process.crawl(FFVBSimpleDebugSpider)
        process.start()
        
        print()
        print("✅ DEBUG TERMINÉ!")
        print()
        print("📊 ANALYSEZ LES RÉSULTATS:")
        print("1. 📄 Ouvrez ffvb_debug_output.csv pour voir tout ce qui a été extrait")
        print("2. 🌐 Ouvrez debug_page_source.html pour voir le code HTML")
        print("3. 🔍 Cherchez les patterns de données des joueurs")
        print()
        
        # Vérifier les fichiers générés
        if os.path.exists('ffvb_debug_output.csv'):
            with open('ffvb_debug_output.csv', 'r', encoding='utf-8') as f:
                lines = sum(1 for line in f) - 1  # -1 pour l'en-tête
            print(f"📈 Éléments extraits: {lines}")
        
        if os.path.exists('debug_page_source.html'):
            size = os.path.getsize('debug_page_source.html')
            print(f"🌐 Taille de la page: {size:,} bytes")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    run_debug_simple()