# run_fixed_scraper.py
import sys
import os
from scrapy.crawler import CrawlerProcess

def run_fixed_scraper():
    """Lance le scraper corrigé pour extraire tous les joueurs"""
    print("🏐 SCRAPER FFVB CORRIGÉ - EXTRACTION DES JOUEURS")
    print("=" * 55)
    print("🎯 Objectifs:")
    print("   ✓ Extraire les images CV des joueurs")
    print("   ✓ Naviguer entre les pages de joueurs") 
    print("   ✓ Collecter les informations disponibles")
    print("   ✓ Gérer les URLs encodées")
    print()
    print("📁 Fichier généré: ffvb_players_fixed.csv")
    print()
    
    # Configuration Scrapy optimisée
    settings = {
        'BOT_NAME': 'ffvb_fixed',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1.5,  # Plus rapide mais respectueux
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        
        # Gestion des erreurs
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        
        # Performance
        'CONCURRENT_REQUESTS': 2,  # Limité pour être respectueux
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        
        # Pas de caching pour avoir les données fraîches
        'HTTPCACHE_ENABLED': False,
        
        # Formats de sortie
        'FEEDS': {
            'ffvb_players_detailed.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 2,
            },
        },
    }
    
    # Ajouter le répertoire actuel au PYTHONPATH
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    process = CrawlerProcess(settings)
    
    try:
        from ffvb_scraper.spiders.ffvb_fixed_spider import FFVBFixedSpider
        
        print("🕷️  Démarrage du scraper corrigé...")
        print("⏳ Cela peut prendre quelques minutes...")
        print()
        
        process.crawl(FFVBFixedSpider)
        process.start()
        
        print()
        print("✅ EXTRACTION TERMINÉE!")
        print()
        
        # Vérifier les résultats
        if os.path.exists('ffvb_players_fixed.csv'):
            with open('ffvb_players_fixed.csv', 'r', encoding='utf-8') as f:
                lines = sum(1 for line in f) - 1  # -1 pour l'en-tête
            print(f"📊 Joueurs trouvés: {lines}")
            
            # Afficher un aperçu
            with open('ffvb_players_fixed.csv', 'r', encoding='utf-8') as f:
                content = f.read()
                print()
                print("📋 Aperçu des données:")
                print(content[:500] + "..." if len(content) > 500 else content)
        
        if os.path.exists('ffvb_players_detailed.json'):
            size = os.path.getsize('ffvb_players_detailed.json')
            print(f"📄 Fichier JSON: {size:,} bytes")
        
        print()
        print("🔍 PROCHAINES ÉTAPES:")
        print("1. Vérifiez ffvb_players_fixed.csv pour les joueurs trouvés")
        print("2. Si peu de joueurs, le site peut utiliser du JavaScript")
        print("3. Considérez utiliser Selenium pour les pages dynamiques")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez que le fichier spider existe dans le bon répertoire")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    run_fixed_scraper()