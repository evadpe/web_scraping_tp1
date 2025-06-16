# run_ffvb_scraper.py
"""
Script de lancement simplifié pour le scraper FFVB
Lance le spider et génère les rapports
"""

import os
import sys
import subprocess
import json
import csv
from datetime import datetime
from pathlib import Path

def check_scrapy_installation():
    """Vérifie que Scrapy est installé"""
    try:
        import scrapy
        print("✅ Scrapy installé")
        return True
    except ImportError:
        print("❌ Scrapy non installé")
        print("📦 Installation: pip install scrapy")
        return False

def check_project_structure():
    """Vérifie et crée la structure du projet Scrapy"""
    required_dirs = [
        'ffvb_scraper',
        'ffvb_scraper/spiders',
    ]
    
    required_files = {
        'ffvb_scraper/__init__.py': '',
        'ffvb_scraper/spiders/__init__.py': '',
        'scrapy.cfg': '''[settings]
default = ffvb_scraper.settings

[deploy]
project = ffvb_scraper
''',
        'ffvb_scraper/settings.py': '''# Settings basiques
BOT_NAME = 'ffvb_scraper'
SPIDER_MODULES = ['ffvb_scraper.spiders']
NEWSPIDER_MODULE = 'ffvb_scraper.spiders'

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5

USER_AGENT = 'ffvb_scraper (+http://educational-purpose.local)'

FEEDS = {
    'ffvb_results.json': {
        'format': 'json',
        'encoding': 'utf8',
        'overwrite': True
    }
}
''',
        'ffvb_scraper/items.py': '''import scrapy

class PlayerItem(scrapy.Item):
    nom_joueur = scrapy.Field()
    numero = scrapy.Field()
    poste = scrapy.Field()
    taille = scrapy.Field()
    poids = scrapy.Field()
    age = scrapy.Field()
    equipe = scrapy.Field()
    url_cv_image = scrapy.Field()
    url_page_principale = scrapy.Field()
    url_source = scrapy.Field()
    date_extraction = scrapy.Field()
''',
        'ffvb_scraper/pipelines.py': '''class BasicPipeline:
    def process_item(self, item, spider):
        return item
'''
    }
    
    print("🔧 Vérification de la structure du projet...")
    
    # Créer les répertoires
    for dir_path in required_dirs:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"📁 {dir_path}")
    
    # Créer les fichiers
    for file_path, content in required_files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📄 {file_path}")
    
    print("✅ Structure du projet créée")

def create_spider_file():
    """Crée le fichier spider dans le bon répertoire"""
    spider_content = '''# ffvb_working_spider.py - Version allégée
import scrapy
import re
from urllib.parse import urljoin
from datetime import datetime

class FFVBWorkingSpider(scrapy.Spider):
    name = 'ffvb'
    allowed_domains = ['ffvb.org']
    start_urls = [
        'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0',
        'http://www.ffvb.org/index.php?lvlid=386&dsgtypid=37&artid=1219&pos=0',
    ]
    
    def __init__(self):
        self.players_found = 0
        
    def parse(self, response):
        self.logger.info(f"🏐 Parsing: {response.url}")
        
        equipe_type = 'Équipe de France Masculine' if 'lvlid=384' in response.url else 'Équipe de France Féminine'
        
        # Chercher tous les éléments contenant potentiellement des joueurs
        containers = response.css('div, tr, li, article, section')
        
        for container in containers:
            text_content = ' '.join(container.css('::text').getall())
            
            # Recherche de noms (mots avec majuscules)
            nom_match = re.search(r'\\b([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\\-\']{2,}(?:\\s+[A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\\-\']{2,})+)\\b', text_content)
            
            if nom_match:
                nom = nom_match.group(1).strip()
                
                # Éviter les faux positifs
                if any(word in nom.lower() for word in ['équipe', 'france', 'volley', 'beach', 'contact', 'mentions']):
                    continue
                
                player_data = {
                    'nom_joueur': nom,
                    'equipe': equipe_type,
                    'url_source': response.url,
                    'date_extraction': datetime.now().isoformat()
                }
                
                # Chercher le numéro
                numero_match = re.search(r'\\b(\\d{1,2})\\b', text_content)
                if numero_match and 1 <= int(numero_match.group(1)) <= 99:
                    player_data['numero'] = numero_match.group(1)
                
                # Chercher le poste
                postes = ['attaquant', 'passeur', 'central', 'libéro', 'réceptionneur']
                for poste in postes:
                    if poste in text_content.lower():
                        player_data['poste'] = poste.title()
                        break
                
                # Chercher les images
                images = container.css('img::attr(src)').getall()
                for img in images:
                    if 'cv' in img.lower() or 'photo' in img.lower():
                        player_data['url_cv_image'] = urljoin(response.url, img)
                        break
                
                self.players_found += 1
                self.logger.info(f"✅ Joueur: {nom}")
                
                yield player_data
        
        # Chercher d'autres pages
        links = response.css('a::attr(href)').getall()
        for link in links:
            if any(param in link for param in ['artid=', 'pos=', 'joueur']):
                yield response.follow(link, self.parse_player_page, meta={'equipe': equipe_type})
    
    def parse_player_page(self, response):
        self.logger.info(f"👤 Page joueur: {response.url}")
        
        # Extraction simple depuis page joueur
        text = ' '.join(response.css('::text').getall())
        
        # Nom depuis titre
        title = response.css('title::text').get() or response.css('h1::text').get() or ''
        nom_match = re.search(r'([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\\s\\-\']+)', title)
        
        if nom_match:
            yield {
                'nom_joueur': nom_match.group(1).strip(),
                'equipe': response.meta.get('equipe', 'Équipe de France'),
                'url_page_principale': response.url,
                'date_extraction': datetime.now().isoformat()
            }
'''
    
    spider_path = 'ffvb_scraper/spiders/ffvb_working_spider.py'
    with open(spider_path, 'w', encoding='utf-8') as f:
        f.write(spider_content)
    
    print(f"🕷️ Spider créé: {spider_path}")

def run_spider():
    """Lance le spider Scrapy"""
    print("\n🚀 LANCEMENT DU SPIDER FFVB")
    print("=" * 40)
    
    try:
        # Changer vers le répertoire du projet
        os.chdir('.')
        
        # Lancer Scrapy
        result = subprocess.run([
            sys.executable, '-m', 'scrapy', 'crawl', 'ffvb',
            '-s', 'LOG_LEVEL=INFO'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Spider terminé avec succès")
            print(result.stdout)
        else:
            print("⚠️ Spider terminé avec erreurs")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - Spider arrêté après 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        return False

def analyze_results():
    """Analyse les résultats du scraping"""
    print("\n📊 ANALYSE DES RÉSULTATS")
    print("=" * 30)
    
    json_files = ['ffvb_results.json', 'ffvb_players_working.json']
    csv_files = ['ffvb_players_working.csv']
    
    total_players = 0
    
    # Analyser JSON
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                count = len(data) if isinstance(data, list) else 1
                total_players += count
                print(f"📄 {json_file}: {count} joueur(s)")
                
                # Afficher quelques exemples
                if isinstance(data, list) and data:
                    print("   Exemples:")
                    for i, player in enumerate(data[:3]):
                        nom = player.get('nom_joueur', 'N/A')
                        equipe = player.get('equipe', 'N/A')
                        print(f"   {i+1}. {nom} ({equipe})")
                
            except Exception as e:
                print(f"⚠️ Erreur lecture {json_file}: {e}")
    
    # Analyser CSV
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                count = len(rows)
                total_players += count
                print(f"📄 {csv_file}: {count} joueur(s)")
                
            except Exception as e:
                print(f"⚠️ Erreur lecture {csv_file}: {e}")
    
    print(f"\n🎯 TOTAL: {total_players} joueur(s) extraits")
    
    if total_players == 0:
        print("\n💡 SUGGESTIONS:")
        print("1. Vérifiez votre connexion internet")
        print("2. Le site FFVB peut avoir changé de structure")
        print("3. Regardez les logs détaillés")
        print("4. Testez sur une page spécifique d'abord")

def main():
    """Fonction principale"""
    print("🏐 FFVB SCRAPER - LANCEMENT AUTOMATIQUE")
    print("=" * 45)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Vérifications préliminaires
    if not check_scrapy_installation():
        return False
    
    check_project_structure()
    create_spider_file()
    
    # Lancer le scraping
    success = run_spider()
    
    # Analyser les résultats
    analyze_results()
    
    if success:
        print("\n🎉 SCRAPING TERMINÉ AVEC SUCCÈS!")
        print("📋 Consultez les fichiers ffvb_results.json et ffvb_players_working.csv")
    else:
        print("\n⚠️ SCRAPING TERMINÉ AVEC ERREURS")
        print("🔍 Consultez les logs pour plus de détails")
    
    return success

if __name__ == "__main__":
    main()