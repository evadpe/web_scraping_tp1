# complete_ffvb_pipeline.py
"""
Pipeline complet pour extraction maximale des données des joueurs FFVB
Combine Scrapy + Selenium + OCR pour récupérer toutes les informations possibles
"""

import os
import sys
import time
import json
import csv
import subprocess
from datetime import datetime
from pathlib import Path

class FFVBCompletePipeline:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"ffvb_extraction_{self.timestamp}"
        self.setup_directories()
        
        self.results = {
            'scrapy_basic': None,
            'scrapy_advanced': None,
            'selenium': None,
            'ocr': None,
            'final_merged': None
        }

    def setup_directories(self):
        """Crée les répertoires de travail"""
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(f"{self.output_dir}/logs").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/raw_data").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/processed").mkdir(exist_ok=True)
        
        print(f"📁 Répertoire de travail: {self.output_dir}")

    def run_complete_extraction(self):
        """Lance le pipeline complet d'extraction"""
        print("🏐 PIPELINE COMPLET FFVB - EXTRACTION MAXIMALE")
        print("=" * 60)
        print(f"🕐 Début: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        steps = [
            ("Scrapy Basique", self.run_scrapy_basic),
            ("Scrapy Avancé", self.run_scrapy_advanced),
            ("Selenium (si nécessaire)", self.run_selenium_if_needed),
            ("OCR Images CV", self.run_ocr_extraction),
            ("Fusion des données", self.merge_all_data),
            ("Rapport final", self.generate_final_report)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 ÉTAPE: {step_name}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                success = step_func()
                elapsed = time.time() - start_time
                
                if success:
                    print(f"✅ {step_name} terminé en {elapsed:.1f}s")
                else:
                    print(f"⚠️ {step_name} partiellement réussi")
                    
            except Exception as e:
                print(f"❌ Erreur {step_name}: {e}")
                # Continuer malgré l'erreur
        
        print(f"\n🎉 PIPELINE TERMINÉ - {datetime.now().strftime('%H:%M:%S')}")
        print(f"📁 Résultats dans: {self.output_dir}")

    def run_scrapy_basic(self):
        """Lance le scraper Scrapy basique"""
        try:
            # Utiliser le scraper corrigé créé précédemment
            from ffvb_scraper.spiders.ffvb_fixed_spider import FFVBFixedSpider
            from scrapy.crawler import CrawlerProcess
            
            settings = {
                'LOG_LEVEL': 'WARNING',
                'FEEDS': {
                    f'{self.output_dir}/raw_data/scrapy_basic.json': {
                        'format': 'json',
                        'encoding': 'utf8'
                    }
                }
            }
            
            process = CrawlerProcess(settings)
            process.crawl(FFVBFixedSpider)
            process.start()
            
            # Vérifier résultats
            basic_file = f'{self.output_dir}/raw_data/scrapy_basic.json'
            if os.path.exists(basic_file):
                with open(basic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.results['scrapy_basic'] = len(data) if isinstance(data, list) else 1
                print(f"📊 Scrapy basique: {self.results['scrapy_basic']} joueur(s)")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur Scrapy basique: {e}")
            return False

    def run_scrapy_advanced(self):
        """Lance le scraper Scrapy avancé"""
        try:
            from ffvb_scraper.spiders.ffvb_advanced_player_scraper import FFVBAdvancedPlayerSpider
            from scrapy.crawler import CrawlerProcess
            
            settings = {
                'LOG_LEVEL': 'WARNING',
                'DOWNLOAD_DELAY': 2,
                'FEEDS': {
                    f'{self.output_dir}/raw_data/scrapy_advanced.json': {
                        'format': 'json',
                        'encoding': 'utf8'
                    }
                }
            }
            
            process = CrawlerProcess(settings)
            process.crawl(FFVBAdvancedPlayerSpider)
            process.start()
            
            # Vérifier résultats
            advanced_file = f'{self.output_dir}/raw_data/scrapy_advanced.json'
            if os.path.exists(advanced_file):
                with open(advanced_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.results['scrapy_advanced'] = len(data) if isinstance(data, list) else 1
                print(f"📊 Scrapy avancé: {self.results['scrapy_advanced']} joueur(s)")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur Scrapy avancé: {e}")
            return False

    def run_selenium_if_needed(self):
        """Lance Selenium si Scrapy n'a pas donné assez de résultats"""
        scrapy_results = (self.results.get('scrapy_basic', 0) + 
                         self.results.get('scrapy_advanced', 0))
        
        if scrapy_results >= 10:  # Seuil acceptable
            print("✅ Scrapy a donné suffisamment de résultats, Selenium non nécessaire")
            return True
        
        print(f"⚠️ Scrapy: seulement {scrapy_results} joueurs, lancement Selenium...")
        
        try:
            from selenium_ffvb_scraper import FFVBSeleniumScraper
            
            scraper = FFVBSeleniumScraper()
            scraper.scrape_players()
            
            # Déplacer le fichier dans notre répertoire
            if os.path.exists('ffvb_players_selenium.csv'):
                import shutil
                shutil.move('ffvb_players_selenium.csv', 
                           f'{self.output_dir}/raw_data/selenium_results.csv')
                
                # Compter les résultats
                with open(f'{self.output_dir}/raw_data/selenium_results.csv', 'r', encoding='utf-8') as f:
                    self.results['selenium'] = sum(1 for line in f) - 1  # -1 pour header
                
                print(f"📊 Selenium: {self.results['selenium']} joueur(s)")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur Selenium: {e}")
            return False

    def run_ocr_extraction(self):
        """Lance l'extraction OCR des images CV"""
        try:
            # Vérifier qu'on a des données de base
            base_files = [
                f'{self.output_dir}/raw_data/scrapy_basic.json',
                f'{self.output_dir}/raw_data/scrapy_advanced.json',
                f'{self.output_dir}/raw_data/selenium_results.csv'
            ]
            
            players_with_images = []
            
            # Collecter toutes les URLs d'images
            for file_path in base_files:
                if os.path.exists(file_path):
                    players_with_images.extend(self.extract_image_urls(file_path))
            
            if not players_with_images:
                print("⚠️ Aucune image CV trouvée pour OCR")
                return False
            
            print(f"🖼️ {len(players_with_images)} image(s) CV à traiter")
            
            # Lancer OCR personnalisé
            ocr_results = []
            
            for i, player_data in enumerate(players_with_images, 1):
                print(f"   [{i}/{len(players_with_images)}] OCR: {player_data.get('nom', 'N/A')}")
                
                try:
                    ocr_data = self.process_single_image_ocr(player_data)
                    if ocr_data:
                        ocr_results.append(ocr_data)
                        
                except Exception as e:
                    print(f"      ❌ Erreur OCR: {e}")
            
            # Sauvegarder résultats OCR
            ocr_file = f'{self.output_dir}/raw_data/ocr_results.json'
            with open(ocr_file, 'w', encoding='utf-8') as f:
                json.dump(ocr_results, f, ensure_ascii=False, indent=2)
            
            self.results['ocr'] = len(ocr_results)
            print(f"📊 OCR: {self.results['ocr']} image(s) traitée(s)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur OCR global: {e}")
            return False

    def extract_image_urls(self, file_path):
        """Extrait les URLs d'images depuis un fichier de données"""
        players = []
        
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    for item in data:
                        if item.get('url_cv_image'):
                            players.append({
                                'nom': item.get('nom_joueur', ''),
                                'numero': item.get('numero', ''),
                                'image_url': item.get('url_cv_image', '')
                            })
            
            elif file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('url_cv_image'):
                            players.append({
                                'nom': row.get('nom_joueur', ''),
                                'numero': row.get('numero', ''),
                                'image_url': row.get('url_cv_image', '')
                            })
        
        except Exception as e:
            print(f"⚠️ Erreur lecture {file_path}: {e}")
        
        return players

    def process_single_image_ocr(self, player_data):
        """Traite une seule image avec OCR"""
        try:
            import requests
            from PIL import Image
            import pytesseract
            import cv2
            import numpy as np
            from io import BytesIO
            import re
            
            # Construire URL complète
            image_url = player_data['image_url']
            if image_url.startswith('/'):
                full_url = f"http://www.ffvb.org{image_url}"
            else:
                full_url = image_url
            
            # Télécharger image
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            
            # Traiter avec OCR
            image = Image.open(BytesIO(response.content))
            
            # Preprocessing simple
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # OCR
            text = pytesseract.image_to_string(gray, config='--psm 6 -l fra')
            
            if not text.strip():
                return None
            
            # Parser le texte pour extraire données
            extracted_data = {
                'nom_joueur': player_data['nom'],
                'numero': player_data['numero'],
                'image_url': full_url,
                'texte_ocr': text.strip(),
                'date_extraction': datetime.now().isoformat()
            }
            
            # Extraction de données spécifiques
            patterns = {
                'poste': r'(?:poste|position)[\s:]+([^,\n\r]+)',
                'taille': r'(?:taille)[\s:]*(\d{1,3})(?:\s*cm)?',
                'poids': r'(?:poids)[\s:]*(\d{2,3})(?:\s*kg)?',
                'age': r'(?:âge|age)[\s:]*(\d{1,2})',
                'club': r'(?:club|équipe)[\s:]+([^,\n\r]+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted_data[field] = match.group(1).strip()
            
            return extracted_data
            
        except Exception as e:
            print(f"      ❌ Erreur traitement image: {e}")
            return None

    def merge_all_data(self):
        """Fusionne toutes les données collectées"""
        print("🔄 Fusion de toutes les sources de données...")
        
        try:
            merged_players = {}
            
            # Sources de données
            sources = {
                'scrapy_basic': f'{self.output_dir}/raw_data/scrapy_basic.json',
                'scrapy_advanced': f'{self.output_dir}/raw_data/scrapy_advanced.json',
                'selenium': f'{self.output_dir}/raw_data/selenium_results.csv',
                'ocr': f'{self.output_dir}/raw_data/ocr_results.json'
            }
            
            # Charger et fusionner chaque source
            for source_name, file_path in sources.items():
                if os.path.exists(file_path):
                    players = self.load_players_from_file(file_path)
                    print(f"   📊 {source_name}: {len(players)} entrée(s)")
                    
                    for player in players:
                        player_key = self.get_player_key(player)
                        
                        if player_key not in merged_players:
                            merged_players[player_key] = {
                                'sources': [],
                                'data': {}
                            }
                        
                        # Ajouter la source
                        merged_players[player_key]['sources'].append(source_name)
                        
                        # Fusionner les données (priorité aux données les plus complètes)
                        for key, value in player.items():
                            if value and value.strip():  # Seulement si non vide
                                existing = merged_players[player_key]['data'].get(key)
                                if not existing or len(str(value)) > len(str(existing)):
                                    merged_players[player_key]['data'][key] = value
            
            # Convertir en liste
            final_players = []
            for player_key, player_info in merged_players.items():
                player_data = player_info['data']
                player_data['sources_fusion'] = ' + '.join(player_info['sources'])
                player_data['score_completude'] = self.calculate_completeness_score(player_data)
                final_players.append(player_data)
            
            # Trier par score de complétude
            final_players.sort(key=lambda x: x.get('score_completude', 0), reverse=True)
            
            # Sauvegarder résultat final
            final_file = f'{self.output_dir}/processed/ffvb_players_final.json'
            with open(final_file, 'w', encoding='utf-8') as f:
                json.dump(final_players, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder aussi en CSV
            self.save_final_csv(final_players)
            
            self.results['final_merged'] = len(final_players)
            print(f"✅ Fusion terminée: {len(final_players)} joueur(s) uniques")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur fusion: {e}")
            return False

    def load_players_from_file(self, file_path):
        """Charge les joueurs depuis un fichier"""
        players = []
        
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        players = data
                    else:
                        players = [data]
            
            elif file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    players = list(reader)
        
        except Exception as e:
            print(f"⚠️ Erreur chargement {file_path}: {e}")
        
        return players

    def get_player_key(self, player):
        """Génère une clé unique pour identifier un joueur"""
        nom = player.get('nom_joueur', '').strip().lower()
        numero = player.get('numero', '').strip()
        
        if nom and numero:
            return f"{nom}_{numero}"
        elif nom:
            return nom
        else:
            return f"unknown_{hash(str(player)) % 10000}"

    def calculate_completeness_score(self, player_data):
        """Calcule un score de complétude des données"""
        important_fields = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age',
            'club_actuel', 'selections', 'matches_joues', 'url_cv_image'
        ]
        
        score = 0
        for field in important_fields:
            if player_data.get(field, '').strip():
                score += 1
        
        return (score / len(important_fields)) * 100

    def save_final_csv(self, players):
        """Sauvegarde le fichier CSV final"""
        csv_file = f'{self.output_dir}/processed/ffvb_players_final.csv'
        
        if not players:
            return
        
        # Obtenir tous les champs possibles
        all_fields = set()
        for player in players:
            all_fields.update(player.keys())
        
        # Ordonner les champs
        ordered_fields = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age',
            'club_actuel', 'selections', 'matches_joues', 'victoires', 'defaites',
            'url_cv_image', 'sources_fusion', 'score_completude'
        ]
        
        # Ajouter les champs restants
        remaining_fields = sorted(all_fields - set(ordered_fields))
        final_fields = ordered_fields + remaining_fields
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=final_fields)
            writer.writeheader()
            writer.writerows(players)

    def generate_final_report(self):
        """Génère le rapport final"""
        print("📋 Génération du rapport final...")
        
        try:
            report_file = f'{self.output_dir}/RAPPORT_FINAL.txt'
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("🏐 RAPPORT FINAL - EXTRACTION FFVB\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"📁 Répertoire: {self.output_dir}\n\n")
                
                f.write("📊 RÉSULTATS PAR MÉTHODE:\n")
                for method, count in self.results.items():
                    if count is not None:
                        f.write(f"   {method}: {count} joueur(s)\n")
                
                f.write(f"\n🎯 TOTAL FINAL: {self.results.get('final_merged', 0)} joueur(s) uniques\n\n")
                
                # Analyse des fichiers générés
                f.write("📁 FICHIERS GÉNÉRÉS:\n")
                for root, dirs, files in os.walk(self.output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        rel_path = os.path.relpath(file_path, self.output_dir)
                        f.write(f"   {rel_path}: {size:,} bytes\n")
                
                f.write("\n✅ EXTRACTION TERMINÉE AVEC SUCCÈS!")
            
            print(f"📄 Rapport sauvegardé: {report_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur rapport: {e}")
            return False

def main():
    """Fonction principale"""
    print("🚀 PIPELINE COMPLET FFVB")
    print("Extraction maximale des données des joueurs")
    print()
    
    # Vérifier les dépendances
    missing_deps = check_dependencies()
    if missing_deps:
        print("❌ Dépendances manquantes:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n📦 Installez avec: pip install " + " ".join(missing_deps))
        return False
    
    try:
        pipeline = FFVBCompletePipeline()
        pipeline.run_complete_extraction()
        
        print(f"\n🎉 SUCCÈS! Consultez le répertoire: {pipeline.output_dir}")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        return False

def check_dependencies():
    """Vérifie les dépendances requises"""
    required = {
        'scrapy': 'scrapy',
        'selenium': 'selenium',
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'pytesseract': 'pytesseract',
        'requests': 'requests'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    return missing

if __name__ == "__main__":
    main()