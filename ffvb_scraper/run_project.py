# run_simple_scraper.py
import sys
import os
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

def run_ffvb_scraper():
    """Lance le scraper FFVB simplifié pour export CSV"""
    print("🏐 SCRAPER FFVB - EXPORT CSV UNIQUEMENT")
    print("=" * 50)
    print("🎯 Objectif: Extraire les données du site FFVB au format CSV")
    print("📁 Fichier de sortie: ffvb_data_export.csv")
    print()
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('ffvb_scraper'):
        print("❌ Répertoire ffvb_scraper non trouvé")
        print("💡 Assurez-vous d'être dans le répertoire parent du projet Scrapy")
        return False
    
    # Ajouter le répertoire du projet au PYTHONPATH
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Configuration Scrapy
    settings = Settings()
    settings.setmodule('ffvb_scraper.settings')
    
    # Paramètres pour un scraping respectueux
    settings.set('LOG_LEVEL', 'INFO')
    settings.set('DOWNLOAD_DELAY', 3)
    settings.set('ROBOTSTXT_OBEY', True)
    settings.set('CONCURRENT_REQUESTS', 1)
    
    # Créer le processus crawler
    process = CrawlerProcess(settings)
    
    try:
        # Importer le spider
        from ffvb_scraper.spiders.ffvb_simple_spider import FFVBSimpleSpider
        
        print("🕷️  Démarrage du scraping...")
        print("⏳ Cela peut prendre 2-5 minutes selon la quantité de données...")
        print("📊 Le fichier CSV se remplit en temps réel")
        print()
        
        # Ajouter le spider et lancer
        process.crawl(FFVBSimpleSpider)
        process.start()  # Bloque jusqu'à la fin
        
        print()
        print("✅ SCRAPING TERMINÉ!")
        print("📄 Fichier généré: ffvb_data_export.csv")
        
        # Vérifier si le fichier existe et donner des stats
        if os.path.exists('ffvb_data_export.csv'):
            with open('ffvb_data_export.csv', 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f) - 1  # -1 pour l'en-tête
            print(f"📈 Nombre de lignes extraites: {line_count}")
            print(f"📋 Colonnes disponibles:")
            print("   - type_donnee (Article, Championnat, Resultat_Historique)")
            print("   - titre, date, contenu, equipe_gagnant, position")
            print("   - region, division, categorie, url_source, date_scraping")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez que ffvb_simple_spider.py est dans ffvb_scraper/spiders/")
        return False
    except Exception as e:
        print(f"❌ Erreur pendant le scraping: {e}")
        return False

def main():
    """Fonction principale"""
    success = run_ffvb_scraper()
    
    if success:
        print()
        print("🎉 EXPORT RÉUSSI!")
        print("💡 Vous pouvez maintenant:")
        print("   1. Ouvrir ffvb_data_export.csv dans Excel/LibreOffice")
        print("   2. Analyser les données avec Python/R")
        print("   3. Créer vos propres visualisations")
        print()
        print("📈 Types de données extraites:")
        print("   • Articles et actualités du volleyball français")
        print("   • Résultats historiques des championnats")
        print("   • Classements actuels par division")
        print("   • Informations géographiques (régions)")
    else:
        print()
        print("❌ Échec de l'export")
        print("💡 Vérifiez la structure du projet et les dépendances")

if __name__ == "__main__":
    main()