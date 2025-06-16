# ocr_cv_extractor.py
"""
Extracteur OCR pour analyser les images CV des joueurs et extraire
toutes les informations textuelles (taille, poids, poste, statistiques, etc.)
"""

import requests
import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
import csv
import json
from urllib.parse import urljoin, unquote
import os
from datetime import datetime

class FFVBOCRExtractor:
    def __init__(self):
        # Configuration OCR
        self.setup_ocr()
        
        # Dictionnaire pour mapper les termes détectés
        self.field_mapping = {
            'poste': ['poste', 'position', 'rôle'],
            'taille': ['taille', 'height', 'cm'],
            'poids': ['poids', 'weight', 'kg'],
            'age': ['âge', 'age', 'ans'],
            'naissance': ['né', 'birth', 'naissance'],
            'club': ['club', 'équipe', 'team'],
            'selection': ['sélection', 'selection', 'caps'],
            'points': ['points', 'pts'],
            'matches': ['matches', 'rencontres', 'games']
        }
        
        # Fichier de sortie
        self.output_file = 'ffvb_players_ocr_enhanced.csv'
        self.setup_output_file()

    def setup_ocr(self):
        """Configure Tesseract OCR"""
        try:
            # Configuration OCR pour le français
            self.ocr_config = '--psm 6 -l fra'
            
            # Test de Tesseract
            test_result = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract version: {test_result}")
            
        except Exception as e:
            print(f"❌ Erreur configuration OCR: {e}")
            print("💡 Installez Tesseract: https://github.com/tesseract-ocr/tesseract")
            raise

    def setup_output_file(self):
        """Initialise le fichier CSV de sortie"""
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'nom_joueur', 'numero', 'poste_ocr', 'taille_ocr', 'poids_ocr', 
                'age_ocr', 'date_naissance_ocr', 'club_ocr', 'selections_ocr',
                'points_ocr', 'matches_ocr', 'autres_stats_ocr', 'texte_complet_ocr',
                'url_image', 'confiance_ocr', 'date_extraction'
            ])

    def process_players_from_csv(self, input_csv='ffvb_players_complete.csv'):
        """Traite tous les joueurs depuis le fichier CSV existant"""
        print("🔍 EXTRACTION OCR DES IMAGES CV")
        print("=" * 40)
        
        if not os.path.exists(input_csv):
            print(f"❌ Fichier {input_csv} non trouvé")
            return
        
        processed_count = 0
        
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        print(f"📊 {len(players)} joueur(s) à traiter")
        print()
        
        for i, player in enumerate(players, 1):
            print(f"🏐 [{i}/{len(players)}] Traitement: {player.get('nom_joueur', 'N/A')}")
            
            image_url = player.get('url_cv_image', '')
            if image_url:
                try:
                    # Construire l'URL complète si nécessaire
                    if image_url.startswith('/'):
                        full_url = f"http://www.ffvb.org{image_url}"
                    else:
                        full_url = image_url
                    
                    # Extraire données OCR
                    ocr_data = self.extract_ocr_from_image_url(full_url)
                    
                    if ocr_data:
                        # Combiner avec données existantes
                        enhanced_player = {
                            'nom_joueur': player.get('nom_joueur', ''),
                            'numero': player.get('numero', ''),
                            **ocr_data,
                            'url_image': full_url,
                            'date_extraction': datetime.now().isoformat()
                        }
                        
                        self.save_enhanced_player(enhanced_player)
                        processed_count += 1
                        
                        print(f"   ✅ OCR réussi - {len(ocr_data)} champs extraits")
                    else:
                        print(f"   ⚠️ Échec OCR")
                
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
            
            else:
                print(f"   ⚠️ Pas d'image CV")
        
        print(f"\n🎉 Traitement terminé: {processed_count}/{len(players)} joueurs traités")

    def extract_ocr_from_image_url(self, image_url):
        """Extrait le texte et les données structurées depuis une URL d'image"""
        try:
            # Télécharger l'image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Convertir en image PIL
            image = Image.open(BytesIO(response.content))
            
            return self.extract_ocr_from_image(image)
        
        except Exception as e:
            print(f"   ❌ Erreur téléchargement image: {e}")
            return None

    def extract_ocr_from_image(self, image):
        """Extrait le texte depuis une image PIL"""
        try:
            # Préprocessing de l'image pour améliorer l'OCR
            processed_image = self.preprocess_image(image)
            
            # Extraction OCR
            text = pytesseract.image_to_string(processed_image, config=self.ocr_config)
            
            if not text.strip():
                return None
            
            # Extraction des données structurées
            structured_data = self.parse_ocr_text(text)
            structured_data['texte_complet_ocr'] = text.strip()
            
            # Calculer confiance OCR
            try:
                data = pytesseract.image_to_data(processed_image, config=self.ocr_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                structured_data['confiance_ocr'] = f"{avg_confidence:.1f}%"
            except:
                structured_data['confiance_ocr'] = "N/A"
            
            return structured_data
        
        except Exception as e:
            print(f"   ❌ Erreur OCR: {e}")
            return None

    def preprocess_image(self, image):
        """Prétraite l'image pour améliorer la qualité OCR"""
        try:
            # Convertir en OpenCV
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convertir en niveaux de gris
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Améliorer le contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Réduire le bruit
            gray = cv2.medianBlur(gray, 3)
            
            # Binarisation adaptive
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Reconvertir en PIL
            processed = Image.fromarray(binary)
            
            return processed
        
        except Exception as e:
            print(f"   ⚠️ Erreur preprocessing: {e}")
            return image  # Retourner image originale si échec

    def parse_ocr_text(self, text):
        """Parse le texte OCR pour extraire des données structurées"""
        data = {}
        
        # Nettoyer le texte
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Patterns d'extraction
        patterns = {
            'poste_ocr': [
                r'(?:poste|position)[\s:]+([^,\n\r]+)',
                r'(attaquant|passeur|central|libéro|libero|réceptionneur|pointu)',
            ],
            'taille_ocr': [
                r'(?:taille|height)[\s:]*(\d{1,3})(?:\s*cm)?',
                r'(\d{3})\s*cm',
                r'(\d\.\d{2})\s*m'
            ],
            'poids_ocr': [
                r'(?:poids|weight)[\s:]*(\d{2,3})(?:\s*kg)?',
                r'(\d{2,3})\s*kg'
            ],
            'age_ocr': [
                r'(?:âge|age)[\s:]*(\d{1,2})(?:\s*ans)?',
                r'(\d{1,2})\s*ans'
            ],
            'date_naissance_ocr': [
                r'(?:né|naissance|birth)[\s:]*([0-9/.-]+)',
                r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})'
            ],
            'club_ocr': [
                r'(?:club|équipe)[\s:]+([^,\n\r]+)',
            ],
            'selections_ocr': [
                r'(?:sélections?|caps?)[\s:]*(\d+)',
                r'(\d+)\s*sélections?'
            ],
            'points_ocr': [
                r'(?:points?)[\s:]*(\d+)',
                r'(\d+)\s*points?'
            ],
            'matches_ocr': [
                r'(?:matches?|rencontres?)[\s:]*(\d+)',
                r'(\d+)\s*matches?'
            ]
        }
        
        # Appliquer les patterns
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    
                    # Nettoyage spécifique par type
                    if field == 'taille_ocr':
                        # Convertir en cm si nécessaire
                        if '.' in value and len(value) <= 4:  # Format 1.85m
                            try:
                                meters = float(value)
                                value = str(int(meters * 100))
                            except:
                                pass
                    
                    elif field == 'poste_ocr':
                        # Normaliser les postes
                        value = self.normalize_position(value)
                    
                    data[field] = value
                    break  # Premier pattern qui matche
        
        # Extraire autres statistiques
        autres_stats = self.extract_other_stats(text)
        if autres_stats:
            data['autres_stats_ocr'] = ' | '.join(autres_stats)
        
        return data

    def normalize_position(self, position):
        """Normalise les noms de postes"""
        position = position.lower().strip()
        
        position_map = {
            'attaquant': 'Attaquant',
            'pointu': 'Attaquant',
            'passeur': 'Passeur',
            'central': 'Central',
            'libéro': 'Libéro',
            'libero': 'Libéro',
            'réceptionneur': 'Réceptionneur-Attaquant',
            'reception': 'Réceptionneur-Attaquant'
        }
        
        for key, value in position_map.items():
            if key in position:
                return value
        
        return position.title()

    def extract_other_stats(self, text):
        """Extrait d'autres statistiques du texte"""
        stats = []
        
        # Patterns pour diverses stats
        stat_patterns = [
            r'(\d+)\s*victoires?',
            r'(\d+)\s*défaites?',
            r'(\d+)\s*sets?',
            r'(\d+)\s*aces?',
            r'(\d+)\s*blocs?',
            r'médaille\s*([^,\n]+)',
            r'champion[ne]?\s*([^,\n]+)',
            r'finaliste\s*([^,\n]+)'
        ]
        
        for pattern in stat_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                stat = match.group(0).strip()
                if len(stat) < 50:  # Éviter les extractions trop longues
                    stats.append(stat)
        
        return stats[:5]  # Limiter à 5 stats

    def save_enhanced_player(self, player_data):
        """Sauvegarde les données enrichies du joueur"""
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                player_data.get('nom_joueur', ''),
                player_data.get('numero', ''),
                player_data.get('poste_ocr', ''),
                player_data.get('taille_ocr', ''),
                player_data.get('poids_ocr', ''),
                player_data.get('age_ocr', ''),
                player_data.get('date_naissance_ocr', ''),
                player_data.get('club_ocr', ''),
                player_data.get('selections_ocr', ''),
                player_data.get('points_ocr', ''),
                player_data.get('matches_ocr', ''),
                player_data.get('autres_stats_ocr', ''),
                player_data.get('texte_complet_ocr', ''),
                player_data.get('url_image', ''),
                player_data.get('confiance_ocr', ''),
                player_data.get('date_extraction', '')
            ])

def main():
    """Fonction principale"""
    print("🖼️  EXTRACTEUR OCR - IMAGES CV JOUEURS FFVB")
    print("=" * 50)
    print("🎯 Objectif: Extraire toutes les données des images CV")
    print("📋 Prérequis: Tesseract OCR installé")
    print()
    
    try:
        # Vérifier les dépendances
        import pytesseract
        from PIL import Image
        import cv2
        from io import BytesIO
        
        extractor = FFVBOCRExtractor()
        extractor.process_players_from_csv()
        
        print("\n✅ EXTRACTION OCR TERMINÉE!")
        print(f"📄 Résultats dans: {extractor.output_file}")
        
        # Analyser les résultats
        analyze_ocr_results(extractor.output_file)
        
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("\n📦 INSTALLATION REQUISE:")
        print("pip install pytesseract opencv-python pillow")
        print("Et installer Tesseract OCR système")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def analyze_ocr_results(filename):
    """Analyse les résultats OCR"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            results = list(reader)
        
        if not results:
            print("❌ Aucun résultat OCR")
            return
        
        print(f"\n📊 ANALYSE OCR - {len(results)} joueur(s)")
        
        # Statistiques de complétude
        fields = ['poste_ocr', 'taille_ocr', 'poids_ocr', 'age_ocr', 'club_ocr']
        
        for field in fields:
            filled = sum(1 for r in results if r.get(field, '').strip())
            percentage = (filled / len(results)) * 100
            print(f"   {field}: {percentage:.1f}% ({filled}/{len(results)})")
        
        # Confiance moyenne OCR
        confidences = []
        for r in results:
            conf_str = r.get('confiance_ocr', '0%')
            if conf_str != 'N/A':
                try:
                    conf = float(conf_str.replace('%', ''))
                    confidences.append(conf)
                except:
                    pass
        
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            print(f"   Confiance OCR moyenne: {avg_conf:.1f}%")
    
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")

if __name__ == "__main__":
    main()