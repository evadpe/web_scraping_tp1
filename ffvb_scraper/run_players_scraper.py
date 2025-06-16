# run_players_scraper.py
import sys
import os
import json
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from datetime import datetime

def setup_directories():
    """Créer les répertoires nécessaires"""
    directories = ['exports', 'logs', 'data']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Répertoire créé: {directory}/")

def run_players_scraper():
    """Lance le scraper pour extraire les données des joueurs FFVB"""
    print("🏐 FFVB PLAYERS SCRAPER - PROJET COMPLET")
    print("=" * 60)
    print("🎯 Objectif: Extraire les données complètes des joueurs FFVB")
    print("📄 URL cible:", 'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0')
    print("🔧 Architecture: Scrapy avec pipelines, middlewares et items")
    print()
    
    # Vérifier la structure du projet
    if not os.path.exists('ffvb_scraper'):
        print("❌ Répertoire ffvb_scraper non trouvé")
        print("💡 Assurez-vous d'être dans le répertoire racine du projet")
        return False
    
    # Créer les répertoires nécessaires
    setup_directories()
    
    # Ajouter le répertoire du projet au PYTHONPATH
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Charger les settings du projet
    settings = get_project_settings()
    
    # Override de certains settings pour ce run spécifique
    settings.update({
        'LOG_FILE': f'logs/ffvb_players_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        'FEEDS': {
            f'exports/ffvb_players_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2,
            }
        }
    })
    
    # Créer le processus crawler
    process = CrawlerProcess(settings)
    
    try:
        # Importer le spider
        from ffvb_scraper.spiders.ffvb_players_spider import FFVBPlayersSpider
        
        print("🕷️  Démarrage du scraping des joueurs...")
        print("⏳ Temps estimé: 5-15 minutes selon la quantité de données")
        print("📊 Pipelines actives:")
        print("   ✅ Validation des données")
        print("   🚫 Filtrage des doublons")
        print("   📄 Export CSV (ffvb_players.csv, ffvb_teams.csv, ffvb_staff.csv)")
        print("   📋 Export JSON (ffvb_data_complete.json)")
        print("   🗄️  Base de données SQLite (ffvb_database.db)")
        print("   📊 Statistiques (ffvb_statistics.json)")
        print()
        print("🔧 Middlewares actifs:")
        print("   🔄 Rotation des User-Agents")
        print("   ⏱️  Throttling intelligent")
        print("   🔁 Retry avec backoff exponentiel")
        print("   📝 Logging détaillé")
        print("   🛡️  Gestion d'erreurs avancée")
        print()
        
        # Lancer le scraping
        process.crawl(FFVBPlayersSpider)
        process.start()
        
        print()
        print("✅ SCRAPING TERMINÉ AVEC SUCCÈS!")
        print()
        
        # Afficher les résultats
        display_results()
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez que ffvb_players_spider.py est dans ffvb_scraper/spiders/")
        return False
    except Exception as e:
        print(f"❌ Erreur pendant le scraping: {e}")
        return False

def display_results():
    """Afficher les résultats du scraping"""
    print("📊 RÉSULTATS DU SCRAPING:")
    print("=" * 40)
    
    # Vérifier les fichiers générés
    files_to_check = [
        ('ffvb_players.csv', 'Joueurs'),
        ('ffvb_teams.csv', 'Équipes'),
        ('ffvb_staff.csv', 'Staff'),
        ('ffvb_data_complete.json', 'Données complètes JSON'),
        ('ffvb_database.db', 'Base de données SQLite'),
        ('ffvb_statistics.json', 'Statistiques')
    ]
    
    for filename, description in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {description}: {filename} ({size:,} bytes)")
            
            # Afficher le nombre de lignes pour les CSV
            if filename.endswith('.csv'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        lines = sum(1 for line in f) - 1  # -1 pour l'en-tête
                    print(f"   📈 Nombre d'entrées: {lines}")
                except:
                    pass
        else:
            print(f"❌ {description}: {filename} - Non créé")
    
    # Afficher les statistiques si disponibles
    if os.path.exists('ffvb_statistics.json'):
        try:
            with open('ffvb_statistics.json', 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            print()
            print("📈 STATISTIQUES DÉTAILLÉES:")
            print(f"   👥 Total joueurs: {stats.get('total_players', 0)}")
            print(f"   🏆 Total équipes: {stats.get('total_teams', 0)}")
            print(f"   👔 Total staff: {stats.get('total_staff', 0)}")
            
            if stats.get('average_height'):
                print(f"   📏 Taille moyenne: {stats['average_height']}cm")
            
            if stats.get('clubs'):
                print(f"   🏛️ Clubs différents: {len(stats['clubs'])}")
            
            # Top 3 des postes
            if stats.get('players_by_position'):
                print("   🎯 Top 3 des postes:")
                sorted_positions = sorted(stats['players_by_position'].items(), 
                                        key=lambda x: x[1], reverse=True)
                for i, (poste, count) in enumerate(sorted_positions[:3], 1):
                    print(f"      {i}. {poste}: {count} joueurs")
                    
        except Exception as e:
            print(f"❌ Erreur lecture statistiques: {e}")
    
    print()
    print("🎉 PROJET SCRAPY TERMINÉ!")
    print("💡 Prochaines étapes:")
    print("   1. 📊 Analysez ffvb_players.csv dans Excel/LibreOffice")
    print("   2. 🗄️  Explorez ffvb_database.db avec DB Browser for SQLite")
    print("   3. 📈 Créez des visualisations avec les statistiques")
    print("   4. 📝 Rédigez votre rapport scolaire")
    print()
    print("🎯 PLUS-VALUE TECHNIQUE:")
    print("   • Architecture Scrapy professionnelle")
    print("   • Middlewares pour rotation UA et gestion erreurs")
    print("   • Pipelines de validation et dédoublonnage")
    print("   • Exports multiples (CSV, JSON, SQLite)")
    print("   • Logging et monitoring complets")
    print("   • Respect de l'éthique du web scraping")

def check_dependencies():
    """Vérifier que toutes les dépendances sont installées"""
    dependencies = [
        'scrapy',
        'itemloaders', 
        'itemadapter'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print("❌ Dépendances manquantes:")
        for dep in missing:
            print(f"   - {dep}")
        print()
        print("💡 Installez-les avec:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🔍 Vérification des dépendances...")
    if not check_dependencies():
        return
    
    success = run_players_scraper()
    
    if success:
        print()
        print("🎊 SUCCÈS COMPLET!")
        print("Votre projet de web scraping avec Scrapy est terminé.")
        print("Tous les fichiers de données sont prêts pour l'analyse.")
    else:
        print()
        print("❌ Échec du scraping")
        print("Consultez les logs pour plus de détails.")

if __name__ == "__main__":
    main()