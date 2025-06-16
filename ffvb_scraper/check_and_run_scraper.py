# check_and_run_scraper.py
"""
Vérifie les fichiers disponibles et lance le scraper de base si nécessaire
"""

import os
import glob
import csv
import sys
from scrapy.crawler import CrawlerProcess

def check_existing_data():
    """Vérifie les données existantes"""
    print("🔍 VÉRIFICATION DES DONNÉES EXISTANTES")
    print("=" * 40)
    
    # Chercher tous les fichiers CSV
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        print("❌ Aucun fichier CSV trouvé")
        return None
    
    print(f"📁 Fichiers CSV trouvés: {len(csv_files)}")
    
    # Analyser chaque fichier
    best_file = None
    best_score = 0
    
    for filename in csv_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)
            
            # Vérifier si c'est un fichier de joueurs FFVB
            has_names = any('nom' in header.lower() for header in headers)
            has_numbers = any('numero' in header.lower() for header in headers)
            has_images = any('url' in header.lower() and 'image' in header.lower() for header in headers)
            
            if has_names and has_numbers:
                # Compter les joueurs avec images
                players_with_images = sum(1 for row in rows 
                                        if row.get('url_cv_image', '').strip())
                
                score = len(rows) + (players_with_images * 2) + (10 if has_images else 0)
                
                print(f"📊 {filename}:")
                print(f"   - Lignes: {len(rows)}")
                print(f"   - Headers: {len(headers)}")
                print(f"   - Avec images CV: {players_with_images}")
                print(f"   - Score: {score}")
                
                if score > best_score:
                    best_score = score
                    best_file = filename
            else:
                print(f"⚠️ {filename}: Pas un fichier de joueurs")
        
        except Exception as e:
            print(f"❌ Erreur lecture {filename}: {e}")
    
    if best_file:
        print(f"\n🏆 MEILLEUR FICHIER: {best_file} (score: {best_score})")
        return best_file
    else:
        print(f"\n❌ Aucun fichier de joueurs valide trouvé")
        return None

def run_base_scraper():
    """Lance le scraper de base pour obtenir les données initiales"""
    print("\n🕷️ LANCEMENT DU SCRAPER DE BASE")
    print("=" * 35)
    
    try:
        # Configuration Scrapy pour scraper de base
        settings = {
            'BOT_NAME': 'ffvb_base',
            'ROBOTSTXT_OBEY': True,
            'DOWNLOAD_DELAY': 2,
            'LOG_LEVEL': 'INFO',
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'FEEDS': {
                'ffvb_players_base.csv': {
                    'format': 'csv',
                    'encoding': 'utf8',
                },
                'ffvb_players_base.json': {
                    'format': 'json',
                    'encoding': 'utf8',
                }
            }
        }
        
        # Ajouter répertoire au path
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Importer et lancer le spider
        try:
            from ffvb_scraper.spiders.ffvb_advanced_player_scraper import FFVBAdvancedPlayerSpider
            spider_available = True
        except ImportError:
            spider_available = False
        
        if spider_available:
            print("✅ Spider trouvé - lancement du scraping...")
            process = CrawlerProcess(settings)
            process.crawl(FFVBAdvancedPlayerSpider)
            process.start()
            
            # Vérifier le résultat
            if os.path.exists('ffvb_players_base.csv'):
                with open('ffvb_players_base.csv', 'r', encoding='utf-8') as f:
                    lines = sum(1 for line in f) - 1  # -1 pour header
                print(f"✅ Scraping réussi: {lines} joueurs dans ffvb_players_base.csv")
                return 'ffvb_players_base.csv'
            else:
                print("❌ Fichier de sortie non créé")
                return None
        else:
            print("❌ Spider non trouvé - utilisation scraper direct")
            return run_direct_scraper()
    
    except Exception as e:
        print(f"❌ Erreur scraper Scrapy: {e}")
        print("🔄 Tentative avec scraper direct...")
        return run_direct_scraper()

def run_direct_scraper():
    """Scraper direct sans Scrapy"""
    print("\n🔍 SCRAPER DIRECT (SANS SCRAPY)")
    print("-" * 30)
    
    import requests
    import re
    from urllib.parse import unquote
    from datetime import datetime
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    players = []
    base_url = "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid="
    
    print("🔍 Recherche des joueurs...")
    
    # Tester une plage d'URLs
    for artid in range(1217, 1235):
        for pos in range(0, 4):
            url = f"{base_url}{artid}&pos={pos}"
            
            try:
                print(f"   Test: artid={artid}, pos={pos}")
                response = session.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Chercher les images CV
                    cv_pattern = r'/data/Files/[^"]*CV%20JOUEURS/(\d+)%20([^"]*?)\.png'
                    matches = re.findall(cv_pattern, response.text)
                    
                    for numero, nom_encoded in matches:
                        nom_decoded = unquote(nom_encoded).replace('%20', ' ').strip()
                        
                        # Éviter doublons
                        if not any(p['nom_joueur'] == nom_decoded for p in players):
                            image_url = f"/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/{numero}%20{nom_encoded}.png"
                            
                            player_data = {
                                'nom_joueur': nom_decoded,
                                'numero': numero,
                                'url_cv_image': image_url,
                                'url_page_principale': url,
                                'date_extraction': datetime.now().isoformat(),
                                'nationalite': 'France',
                                'competitions': 'Équipe de France',
                                'bio_courte': f'Joueur de l\'équipe de France masculine #{numero}',
                                'urls_stats': url
                            }
                            
                            players.append(player_data)
                            print(f"      ✅ Trouvé: {nom_decoded} (#{numero})")
                
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ Erreur {url}: {e}")
                continue
    
    if players:
        # Sauvegarder en CSV
        output_file = 'ffvb_players_complete.csv'
        
        headers = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age', 'date_naissance',
            'club_actuel', 'club_precedent', 'nationalite', 'selections', 'points_totaux',
            'matches_joues', 'victoires', 'defaites', 'ratio_victoires', 'derniere_selection',
            'competitions', 'titres', 'distinctions', 'bio_courte', 'url_cv_image',
            'url_page_principale', 'urls_stats', 'date_extraction'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for player in players:
                writer.writerow(player)
        
        print(f"\n✅ Scraper direct réussi: {len(players)} joueurs")
        print(f"📄 Fichier créé: {output_file}")
        return output_file
    else:
        print("\n❌ Aucun joueur trouvé avec le scraper direct")
        return None

def main():
    """Fonction principale"""
    print("🏐 VÉRIFICATION ET SCRAPING DE BASE FFVB")
    print("Prépare les données pour l'extraction OCR")
    print()
    
    # 1. Vérifier les données existantes
    existing_file = check_existing_data()
    
    if existing_file:
        print(f"\n✅ DONNÉES EXISTANTES TROUVÉES: {existing_file}")
        
        choice = input("\nUtiliser ce fichier ou re-scraper? (u/r): ").strip().lower()
        
        if choice == 'u':
            print(f"📊 Utilisation de {existing_file}")
            print(f"\n🚀 PROCHAINE ÉTAPE:")
            print(f"   python complete_data_extraction.py")
            print(f"   OU")
            print(f"   python final_ocr_extractor_optimized.py")
            return
    
    # 2. Lancer le scraping de base
    print(f"\n🔄 LANCEMENT DU SCRAPING DE BASE...")
    result_file = run_base_scraper()
    
    if result_file:
        print(f"\n🎉 SCRAPING TERMINÉ AVEC SUCCÈS!")
        print(f"📄 Fichier créé: {result_file}")
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        print(f"1. python complete_data_extraction.py")
        print(f"2. OU directement: python final_ocr_extractor_optimized.py")
    else:
        print(f"\n❌ ÉCHEC DU SCRAPING")
        print(f"💡 Vérifiez votre connexion internet et les dépendances")

if __name__ == "__main__":
    main()