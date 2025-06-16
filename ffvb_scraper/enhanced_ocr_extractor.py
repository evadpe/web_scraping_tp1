# enhanced_ocr_extractor.py
"""
Extracteur OCR optimisé pour récupérer TOUTES les données manquantes
depuis les images CV des 51 joueurs extraits
"""

import requests
import csv
import json
import re
import os
from urllib.parse import unquote
from datetime import datetime
import time

# Tentative d'import OCR (optionnel)
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
    print("✅ OCR disponible (Tesseract)")
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR non disponible - extraction basique uniquement")

class EnhancedOCRExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.output_file = 'ffvb_players_enhanced_complete.csv'
        self.failed_extractions = []
        self.success_count = 0
        
        # Patterns d'extraction améliorés
        self.extraction_patterns = {
            'poste': [
                r'(?:poste|position)[\s:]*([^,\n\r\.]+)',
                r'(attaquant|passeur|central|libéro|libero|réceptionneur|pointu|opposite)',
                r'(réceptionneur[-\s]?attaquant|central[-\s]?bloqueur)'
            ],
            'taille': [
                r'(?:taille|height)[\s:]*(\d{1,3})(?:\s*cm)?',
                r'(\d{3})\s*cm',
                r'(\d\.\d{2})\s*m',
                r'(\d{1,3})\s*centimètres?'
            ],
            'poids': [
                r'(?:poids|weight|masse)[\s:]*(\d{2,3})(?:\s*kg)?',
                r'(\d{2,3})\s*kg',
                r'(\d{2,3})\s*kilos?'
            ],
            'age': [
                r'(?:âge|age)[\s:]*(\d{1,2})(?:\s*ans?)?',
                r'(\d{1,2})\s*ans?',
                r'(\d{1,2})\s*years?\s*old'
            ],
            'naissance': [
                r'(?:né|naissance|birth|born)[\s:]*([0-9\/\.-]+)',
                r'(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{4})',
                r'(\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})'
            ],
            'club': [
                r'(?:club|équipe|team|club actuel)[\s:]+([^,\n\r\.]+)',
                r'(?:joue à|évolue à|en club à)[\s:]*([^,\n\r\.]+)'
            ],
            'selections': [
                r'(?:sélections?|caps?|international)[\s:]*(\d+)',
                r'(\d+)\s*sélections?',
                r'(\d+)\s*caps?'
            ]
        }

    def process_all_players(self, input_csv='ffvb_players_complete.csv'):
        """Traite tous les joueurs du CSV d'entrée"""
        print("🖼️ EXTRACTION OCR COMPLÈTE - DONNÉES MANQUANTES")
        print("=" * 55)
        
        if not os.path.exists(input_csv):
            print(f"❌ Fichier {input_csv} non trouvé")
            return False
        
        # Lire les joueurs existants
        players = self.load_players(input_csv)
        print(f"📊 {len(players)} joueur(s) à traiter")
        
        if not players:
            print("❌ Aucun joueur trouvé")
            return False
        
        # Initialiser le fichier de sortie
        self.initialize_output_file()
        
        # Traiter chaque joueur
        for i, player in enumerate(players, 1):
            print(f"\n🏐 [{i}/{len(players)}] {player.get('nom_joueur', 'N/A')} (#{player.get('numero', 'N/A')})")
            
            try:
                enhanced_data = self.extract_player_complete_data(player)
                self.save_enhanced_player(enhanced_data)
                self.success_count += 1
                
                # Pause respectueuse
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                self.failed_extractions.append({
                    'player': player.get('nom_joueur', 'N/A'),
                    'error': str(e)
                })
        
        # Résumé final
        self.print_final_summary(len(players))
        return True

    def load_players(self, csv_file):
        """Charge les joueurs depuis le CSV"""
        players = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                players = [row for row in reader if row.get('nom_joueur')]
        
        except Exception as e:
            print(f"❌ Erreur lecture {csv_file}: {e}")
        
        return players

    def extract_player_complete_data(self, player):
        """Extrait toutes les données possibles pour un joueur"""
        enhanced_data = player.copy()  # Partir des données existantes
        
        # 1. Extraction depuis image CV (si OCR disponible)
        if OCR_AVAILABLE and player.get('url_cv_image'):
            ocr_data = self.extract_from_cv_image(player['url_cv_image'])
            enhanced_data.update(ocr_data)
        
        # 2. Extraction depuis URL de nom de fichier (fallback)
        filename_data = self.extract_from_filename(player.get('url_cv_image', ''))
        enhanced_data.update(filename_data)
        
        # 3. Nettoyage et validation des données
        enhanced_data = self.clean_and_validate_data(enhanced_data)
        
        # 4. Score de complétude
        enhanced_data['completeness_score'] = self.calculate_completeness_score(enhanced_data)
        
        return enhanced_data

    def extract_from_cv_image(self, image_url):
        """Extrait les données depuis l'image CV avec OCR"""
        if not image_url:
            return {}
        
        try:
            # Construire URL complète
            if image_url.startswith('/'):
                full_url = f"http://www.ffvb.org{image_url}"
            else:
                full_url = image_url
            
            print(f"   🖼️ Téléchargement image: {full_url}")
            
            # Télécharger image
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            # Traiter avec OCR
            from io import BytesIO
            image = Image.open(BytesIO(response.content))
            
            # Préprocessing pour améliorer OCR
            processed_image = self.enhance_image_for_ocr(image)
            
            # Extraction OCR
            text = pytesseract.image_to_string(processed_image, config='--psm 6 -l fra')
            
            if not text.strip():
                print("   ⚠️ Aucun texte détecté dans l'image")
                return {'raw_ocr_text': ''}
            
            print(f"   ✅ OCR réussi - {len(text)} caractères extraits")
            
            # Parser le texte pour extraire données structurées
            structured_data = self.parse_ocr_text(text)
            structured_data['raw_ocr_text'] = text.strip()
            
            return structured_data
        
        except Exception as e:
            print(f"   ❌ Erreur OCR: {e}")
            return {'ocr_error': str(e)}

    def enhance_image_for_ocr(self, image):
        """Améliore la qualité de l'image pour l'OCR"""
        try:
            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Redimensionner si trop petit
            width, height = image.size
            if width < 1000:
                scale_factor = 1000 / width
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Améliorer le contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Améliorer la netteté
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            # Convertir en niveaux de gris pour OCR
            image = image.convert('L')
            
            # Utiliser OpenCV pour nettoyage avancé
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_GRAY2BGR)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Débruitage
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Binarisation adaptative
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Reconvertir en PIL
            final_image = Image.fromarray(binary)
            
            return final_image
        
        except Exception as e:
            print(f"   ⚠️ Erreur preprocessing image: {e}")
            return image

    def parse_ocr_text(self, text):
        """Parse le texte OCR pour extraire des données structurées"""
        data = {}
        
        # Nettoyer le texte
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Appliquer tous les patterns d'extraction
        for field, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    
                    # Post-traitement spécifique par champ
                    processed_value = self.post_process_field(field, value, text)
                    if processed_value:
                        data[field] = processed_value
                        print(f"   📋 {field}: {processed_value}")
                        break  # Premier pattern qui matche
        
        # Extraire statistiques additionnelles
        stats = self.extract_additional_stats(text)
        data.update(stats)
        
        return data

    def post_process_field(self, field, value, full_text):
        """Post-traite une valeur extraite selon le type de champ"""
        if field == 'taille':
            # Normaliser en cm
            if '.' in value and len(value) <= 4:  # Format 1.85m
                try:
                    meters = float(value)
                    return str(int(meters * 100))
                except:
                    pass
            elif value.isdigit() and len(value) == 3:  # Format 185cm
                return value
        
        elif field == 'poste':
            # Normaliser les postes
            poste_map = {
                'attaquant': 'Attaquant',
                'pointu': 'Attaquant',
                'opposite': 'Attaquant (Opposite)',
                'passeur': 'Passeur',
                'central': 'Central',
                'libéro': 'Libéro',
                'libero': 'Libéro',
                'réceptionneur': 'Réceptionneur-Attaquant'
            }
            
            value_lower = value.lower()
            for key, mapped_value in poste_map.items():
                if key in value_lower:
                    return mapped_value
            
            return value.title()
        
        elif field == 'poids':
            # S'assurer que c'est un nombre valide
            if value.isdigit() and 50 <= int(value) <= 150:
                return value
        
        elif field == 'age':
            # Valider l'âge
            if value.isdigit() and 16 <= int(value) <= 45:
                return value
        
        elif field == 'club':
            # Nettoyer le nom du club
            value = re.sub(r'\s+', ' ', value).strip()
            if len(value) > 3 and len(value) < 50:
                return value
        
        return value if len(value) > 0 else None

    def extract_additional_stats(self, text):
        """Extrait des statistiques additionnelles du texte"""
        stats = {}
        
        # Patterns pour statistiques
        stat_patterns = {
            'matches_totaux': r'(\d+)\s*(?:matches?|rencontres?)',
            'points_marques': r'(\d+)\s*points?',
            'victoires': r'(\d+)\s*victoires?',
            'tournois': r'(\d+)\s*tournois?',
            'titres': r'(\d+)\s*titres?'
        }
        
        for stat_name, pattern in stat_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                if value.isdigit() and int(value) < 10000:  # Validation basique
                    stats[stat_name] = value
        
        return stats

    def extract_from_filename(self, image_url):
        """Extrait des infos depuis le nom de fichier (fallback)"""
        if not image_url:
            return {}
        
        try:
            # Décoder l'URL
            decoded_url = unquote(image_url)
            
            # Extraire le nom depuis le pattern CV JOUEURS
            match = re.search(r'CV\s+JOUEURS/(\d+)\s+([^/]+?)\.png', decoded_url, re.IGNORECASE)
            
            if match:
                return {
                    'numero_from_filename': match.group(1),
                    'nom_from_filename': match.group(2).strip()
                }
        
        except Exception as e:
            print(f"   ⚠️ Erreur extraction filename: {e}")
        
        return {}

    def clean_and_validate_data(self, data):
        """Nettoie et valide les données extraites"""
        cleaned = {}
        
        for key, value in data.items():
            if value and str(value).strip():
                cleaned_value = str(value).strip()
                
                # Validation spécifique par champ
                if key in ['taille', 'poids', 'age', 'numero'] and not cleaned_value.isdigit():
                    continue  # Ignorer les valeurs non numériques
                
                if key == 'taille' and (not cleaned_value.isdigit() or not 150 <= int(cleaned_value) <= 220):
                    continue  # Taille réaliste
                
                if key == 'poids' and (not cleaned_value.isdigit() or not 60 <= int(cleaned_value) <= 130):
                    continue  # Poids réaliste
                
                cleaned[key] = cleaned_value
        
        return cleaned

    def calculate_completeness_score(self, data):
        """Calcule un score de complétude des données"""
        important_fields = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 
            'age', 'club', 'selections'
        ]
        
        filled_count = sum(1 for field in important_fields if data.get(field))
        return round((filled_count / len(important_fields)) * 100, 1)

    def initialize_output_file(self):
        """Initialise le fichier CSV de sortie"""
        headers = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age', 'naissance',
            'club', 'selections', 'matches_totaux', 'points_marques', 'victoires',
            'url_cv_image', 'completeness_score', 'raw_ocr_text', 'extraction_method',
            'date_extraction'
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def save_enhanced_player(self, data):
        """Sauvegarde les données enrichies"""
        row_data = [
            data.get('nom_joueur', ''),
            data.get('numero', ''),
            data.get('poste', ''),
            data.get('taille', ''),
            data.get('poids', ''),
            data.get('age', ''),
            data.get('naissance', ''),
            data.get('club', ''),
            data.get('selections', ''),
            data.get('matches_totaux', ''),
            data.get('points_marques', ''),
            data.get('victoires', ''),
            data.get('url_cv_image', ''),
            data.get('completeness_score', 0),
            data.get('raw_ocr_text', '')[:500],  # Limiter la longueur
            'OCR' if OCR_AVAILABLE else 'Basic',
            datetime.now().isoformat()
        ]
        
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row_data)

    def print_final_summary(self, total_players):
        """Affiche le résumé final"""
        print(f"\n🎉 EXTRACTION TERMINÉE!")
        print("=" * 30)
        print(f"📊 Joueurs traités: {total_players}")
        print(f"✅ Succès: {self.success_count}")
        print(f"❌ Échecs: {len(self.failed_extractions)}")
        print(f"📄 Résultats dans: {self.output_file}")
        
        if self.failed_extractions:
            print(f"\n⚠️ Échecs détaillés:")
            for failure in self.failed_extractions[:5]:  # Max 5
                print(f"   - {failure['player']}: {failure['error']}")

def main():
    """Fonction principale"""
    print("🔍 EXTRACTEUR OCR OPTIMISÉ FFVB")
    print("Récupération des données manquantes depuis les images CV")
    print()
    
    if not OCR_AVAILABLE:
        print("⚠️ OCR non disponible - extraction basique uniquement")
        print("📦 Pour OCR complet, installez: pip install pytesseract opencv-python pillow")
        print()
    
    try:
        extractor = EnhancedOCRExtractor()
        success = extractor.process_all_players()
        
        if success:
            print(f"\n✅ EXTRACTION RÉUSSIE!")
            print(f"📋 Consultez: {extractor.output_file}")
        else:
            print(f"\n❌ EXTRACTION ÉCHOUÉE")
    
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()