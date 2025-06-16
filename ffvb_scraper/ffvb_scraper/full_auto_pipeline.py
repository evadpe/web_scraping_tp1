# full_auto_pipeline.py
"""
Pipeline automatique complet FFVB
1. Scraping des données de base (noms, numéros, URLs images)
2. Nettoyage des doublons
3. Extraction OCR des données complètes
4. Production du CSV final
"""

import os
import sys
import subprocess
import time
from scrapy.crawler import CrawlerProcess

def run_complete_pipeline():
    """Lance le pipeline complet automatiquement"""
    print("🏐 PIPELINE AUTOMATIQUE COMPLET FFVB")
    print("=" * 50)
    print("🎯 Objectif: CSV final avec toutes les données des joueurs")
    print("🔄 Étapes: Scraping → Nettoyage → OCR → CSV final")
    print()
    
    try:
        # Étape 1: Scraping des données de base
        step1_success = run_initial_scraping()
        
        if not step1_success:
            print("❌ Échec étape 1 - Scraping de base")
            return False
        
        # Étape 2: Nettoyage des doublons
        step2_success = run_cleaning()
        
        # Étape 3: Extraction OCR complète
        step3_success = run_ocr_extraction()
        
        if step3_success:
            print("\n🎉 PIPELINE TERMINÉ AVEC SUCCÈS!")
            print("📄 Fichier final: FFVB_JOUEURS_COMPLET.csv")
            analyze_final_results()
        else:
            print("\n⚠️ Pipeline partiellement réussi")
            print("📊 Vérifiez les fichiers générés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {e}")
        return False

def run_initial_scraping():
    """Étape 1: Scraping des données de base"""
    print("\n📊 ÉTAPE 1: SCRAPING DES DONNÉES DE BASE")
    print("-" * 50)
    
    try:
        # Configuration Scrapy
        settings = {
            'BOT_NAME': 'ffvb_auto',
            'ROBOTSTXT_OBEY': True,
            'DOWNLOAD_DELAY': 2,
            'LOG_LEVEL': 'WARNING',  # Moins de logs pour pipeline auto
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        # Ajouter le répertoire au PYTHONPATH
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        process = CrawlerProcess(settings)
        
        # Importer et lancer le spider
        from spiders.ffvb_advanced_player_scraper import FFVBAdvancedPlayerSpider
        
        print("🕷️ Démarrage du scraping...")
        print("⏳ Extraction des noms, numéros et URLs des images CV...")
        
        process.crawl(FFVBAdvancedPlayerSpider)
        process.start()
        
        # Vérifier le résultat
        if os.path.exists('ffvb_players_complete.csv'):
            with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
                lines = sum(1 for line in f) - 1  # -1 pour header
            
            print(f"✅ Scraping réussi: {lines} joueurs extraits")
            return True
        else:
            print("❌ Fichier de sortie non trouvé")
            return False
    
    except Exception as e:
        print(f"❌ Erreur scraping: {e}")
        return False

def run_cleaning():
    """Étape 2: Nettoyage des doublons"""
    print("\n🧹 ÉTAPE 2: NETTOYAGE DES DOUBLONS")
    print("-" * 50)
    
    if not os.path.exists('ffvb_players_complete.csv'):
        print("⚠️ Pas de fichier à nettoyer")
        return False
    
    try:
        # Lancer le nettoyage via subprocess pour éviter les conflits
        result = subprocess.run([
            sys.executable, 'clean_duplicates.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Nettoyage réussi")
            return True
        else:
            print(f"⚠️ Nettoyage avec erreurs: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return False

def run_ocr_extraction():
    """Étape 3: Extraction OCR complète"""
    print("\n🖼️ ÉTAPE 3: EXTRACTION OCR COMPLÈTE")
    print("-" * 50)
    
    # Vérifier qu'on a des données à traiter
    data_files = ['ffvb_players_clean.csv', 'ffvb_players_complete.csv']
    data_file = None
    
    for file in data_files:
        if os.path.exists(file):
            data_file = file
            break
    
    if not data_file:
        print("❌ Aucun fichier de données trouvé")
        return False
    
    try:
        # Lancer l'extraction OCR directement
        extractor = FFVBAutoExtractor()
        extractor.input_file = data_file
        success = extractor.run_extraction()
        
        if success:
            print("✅ Extraction OCR réussie")
            return True
        else:
            print("⚠️ Extraction OCR partielle")
            return False
    
    except Exception as e:
        print(f"❌ Erreur extraction OCR: {e}")
        return False

def analyze_final_results():
    """Analyse les résultats finaux"""
    print("\n📈 ANALYSE DES RÉSULTATS FINAUX")
    print("-" * 40)
    
    if os.path.exists('FFVB_JOUEURS_COMPLET.csv'):
        try:
            import csv
            
            with open('FFVB_JOUEURS_COMPLET.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                players = list(reader)
            
            print(f"👥 Total joueurs: {len(players)}")
            
            # Analyser la complétude
            if players:
                fields = ['poste', 'taille', 'poids', 'club']
                print(f"\n📊 COMPLÉTUDE DES DONNÉES:")
                
                for field in fields:
                    filled = sum(1 for p in players if p.get(field, '').strip())
                    percentage = (filled / len(players)) * 100
                    print(f"   {field:10}: {filled:2d}/{len(players)} ({percentage:5.1f}%)")
                
                # Quelques exemples
                print(f"\n🏐 EXEMPLES DE JOUEURS:")
                for i, player in enumerate(players[:3], 1):
                    name = player.get('nom_joueur', 'N/A')
                    poste = player.get('poste', 'N/A')
                    taille = player.get('taille', 'N/A')
                    print(f"   {i}. {name} - {poste}, {taille}cm")
        
        except Exception as e:
            print(f"⚠️ Erreur analyse: {e}")

# Classe d'extraction OCR simplifiée pour le pipeline
class FFVBAutoExtractor:
    def __init__(self):
        self.input_file = None
        self.output_file = 'FFVB_JOUEURS_COMPLET.csv'
        
    def run_extraction(self):
        """Lance l'extraction OCR automatique"""
        try:
            # Importer les modules OCR
            import pytesseract
            from PIL import Image
            import requests
            import re
            import csv
            from datetime import datetime
            from io import BytesIO
            
            # Configuration OCR
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            
            # Charger les données
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                players = list(reader)
            
            print(f"📊 {len(players)} joueurs à traiter")
            
            # Initialiser le fichier de sortie
            self.init_output_file()
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            success_count = 0
            
            # Traiter chaque joueur
            for i, player in enumerate(players, 1):
                name = player.get('nom_joueur', 'N/A')
                print(f"🏐 [{i:2d}/{len(players)}] {name}")
                
                try:
                    # Extraction OCR
                    enhanced_player = self.extract_player_data(player, session)
                    
                    # Sauvegarder
                    self.save_player(enhanced_player)
                    
                    if enhanced_player.get('ocr_success'):
                        success_count += 1
                        
                    # Pause
                    time.sleep(1)
                
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
                    self.save_player(player)  # Sauvegarder au moins les données de base
            
            print(f"\n✅ Extraction terminée: {success_count}/{len(players)} réussies")
            return True
            
        except Exception as e:
            print(f"❌ Erreur extraction: {e}")
            return False
    
    def extract_player_data(self, player, session):
        """Extrait les données d'un joueur"""
        enhanced = player.copy()
        enhanced['ocr_success'] = False
        enhanced['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        image_url = player.get('url_cv_image', '').strip()
        if image_url:
            try:
                # URL complète
                if image_url.startswith('/'):
                    full_url = f"http://www.ffvb.org{image_url}"
                else:
                    full_url = image_url
                
                # Télécharger et traiter
                response = session.get(full_url, timeout=10)
                response.raise_for_status()
                
                image = Image.open(BytesIO(response.content))
                text = pytesseract.image_to_string(image, config='--psm 6 -l eng')
                
                if text.strip():
                    # Parser le texte
                    ocr_data = self.parse_text_simple(text)
                    enhanced.update(ocr_data)
                    enhanced['ocr_success'] = True
                    
                    # Afficher résumé
                    found = [k for k, v in ocr_data.items() if v]
                    if found:
                        print(f"   ✅ Trouvé: {', '.join(found[:3])}")
                    else:
                        print(f"   ⚠️ Texte extrait mais aucune donnée structurée")
                else:
                    print(f"   ⚠️ Aucun texte extrait")
            
            except Exception as e:
                print(f"   ❌ OCR échoué: {e}")
        
        return enhanced
    
    def parse_text_simple(self, text):
        """Parse simple du texte OCR"""
        data = {}
        
        # Patterns basiques
        patterns = {
            'poste': r'\b(ATTAQUANT|PASSEUR|CENTRAL|LIBÉRO|RÉCEPTIONNEUR)\b',
            'taille': r'\b(1[7-9]\d|20\d)\b',
            'poids': r'\b([6-9]\d|1[0-2]\d)\b(?:\s*kg)?',
            'club': r'\b([A-Z]{3,15}(?:\s+[A-Z]{3,15})*)\b'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                
                # Validation basique
                if field == 'taille' and 170 <= int(value) <= 220:
                    data[field] = value
                elif field == 'poids' and 60 <= int(value) <= 130:
                    data[field] = value
                elif field in ['poste', 'club'] and len(value) >= 3:
                    data[field] = value.title()
        
        return data
    
    def init_output_file(self):
        """Initialise le fichier de sortie"""
        headers = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age',
            'club', 'url_cv_image', 'ocr_success', 'extraction_date'
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def save_player(self, player):
        """Sauvegarde un joueur"""
        row = [
            player.get('nom_joueur', ''),
            player.get('numero', ''),
            player.get('poste', ''),
            player.get('taille', ''),
            player.get('poids', ''),
            player.get('age', ''),
            player.get('club', ''),
            player.get('url_cv_image', ''),
            player.get('ocr_success', False),
            player.get('extraction_date', '')
        ]
        
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

def main():
    """Fonction principale"""
    print("🏐 PIPELINE AUTOMATIQUE FFVB")
    print("Du scraping au CSV final en une seule commande")
    print()
    
    # Vérifier les prérequis
    if not check_prerequisites():
        return
    
    # Demander confirmation
    print("🚀 Prêt à lancer le pipeline complet?")
    print("   1. Scraping des données de base (~5 min)")
    print("   2. Nettoyage des doublons (~1 min)")  
    print("   3. Extraction OCR complète (~15 min)")
    print()
    
    choice = input("Continuer? (o/n): ").strip().lower()
    
    if choice == 'o':
        start_time = time.time()
        success = run_complete_pipeline()
        elapsed = time.time() - start_time
        
        print(f"\n⏱️ Temps total: {elapsed/60:.1f} minutes")
        
        if success:
            print("🎉 PIPELINE RÉUSSI!")
            print("📄 Votre fichier: FFVB_JOUEURS_COMPLET.csv")
        else:
            print("⚠️ Pipeline incomplet - vérifiez les logs")
    else:
        print("👋 Annulé")

def check_prerequisites():
    """Vérifie les prérequis"""
    try:
        import scrapy
        import pytesseract
        print("✅ Modules requis disponibles")
        return True
    except ImportError as e:
        print(f"❌ Module manquant: {e}")
        print("📦 Installez: pip install scrapy pytesseract pillow opencv-python")
        return False

if __name__ == "__main__":
    main()