# extract_final_data.py
"""
Script final pour extraire toutes les données depuis vos fichiers existants
Produit un CSV complet avec toutes les informations des joueurs
"""

import csv
import os
import requests
import re
import time
from datetime import datetime
from io import BytesIO
import pytesseract
from PIL import Image, ImageEnhance
import cv2
import numpy as np

# Configuration OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class FFVBFinalExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Fichier de sortie final
        self.output_file = 'FFVB_JOUEURS_COMPLET.csv'
        self.players_processed = 0
        self.successful_extractions = 0

    def run_complete_extraction(self):
        """Lance l'extraction complète"""
        print("🏐 EXTRACTION FINALE DONNÉES FFVB")
        print("=" * 40)
        print("🎯 Objectif: CSV complet avec toutes les données")
        print()
        
        # 1. Charger les données existantes
        players = self.load_existing_data()
        if not players:
            print("❌ Aucune donnée trouvée")
            return
        
        print(f"📊 {len(players)} joueurs à traiter")
        print(f"📄 Fichier de sortie: {self.output_file}")
        print()
        
        # 2. Initialiser le fichier final
        self.init_final_csv()
        
        # 3. Traiter chaque joueur
        for i, player in enumerate(players, 1):
            name = player.get('nom_joueur', 'N/A')
            numero = player.get('numero', 'N/A')
            
            print(f"🏐 [{i:2d}/{len(players)}] {name} (#{numero})")
            
            try:
                # Extraction OCR + données existantes
                complete_player = self.extract_complete_player_data(player)
                
                # Sauvegarder dans le CSV final
                self.save_to_final_csv(complete_player)
                
                # Afficher résumé
                self.show_extraction_summary(complete_player)
                
                self.players_processed += 1
                if complete_player.get('extraction_success'):
                    self.successful_extractions += 1
                
                # Pause respectueuse
                time.sleep(1.5)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                # Sauvegarder au moins les données de base
                self.save_to_final_csv(player)
        
        # 4. Résumé final
        self.show_final_summary(len(players))

    def load_existing_data(self):
        """Charge les données depuis le meilleur fichier disponible"""
        # Ordre de priorité des fichiers
        possible_files = [
            'ffvb_players_clean.csv',           # Données nettoyées (préféré)
            'ffvb_players_complete.csv',        # Données complètes originales
            'ffvb_joueurs_donnees_completes.csv',  # Autres variants
            'ffvb_joueurs_donnees_optimisees.csv'
        ]
        
        for filename in possible_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        players = [row for row in reader if row.get('nom_joueur', '').strip()]
                    
                    print(f"📂 Fichier source: {filename}")
                    print(f"👥 Joueurs trouvés: {len(players)}")
                    
                    # Vérifier qu'on a les URLs d'images
                    with_images = sum(1 for p in players if p.get('url_cv_image', '').strip())
                    print(f"🖼️ Avec images CV: {with_images}/{len(players)}")
                    
                    return players
                    
                except Exception as e:
                    print(f"⚠️ Erreur lecture {filename}: {e}")
                    continue
        
        print("❌ Aucun fichier de données trouvé")
        print("💡 Fichiers recherchés:", ", ".join(possible_files))
        return []

    def extract_complete_player_data(self, player):
        """Extrait toutes les données possibles pour un joueur"""
        # Partir des données existantes
        complete_data = player.copy()
        
        # Ajouter métadonnées
        complete_data['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        complete_data['extraction_success'] = False
        complete_data['extraction_method'] = 'none'
        
        # Extraction OCR si image disponible
        image_url = player.get('url_cv_image', '').strip()
        if image_url:
            ocr_data = self.extract_from_cv_image(image_url, player.get('nom_joueur', ''))
            
            if ocr_data:
                # Fusionner les données OCR
                for key, value in ocr_data.items():
                    if value and value.strip():  # Seulement si non vide
                        complete_data[key] = value
                
                complete_data['extraction_success'] = True
                complete_data['extraction_method'] = ocr_data.get('ocr_method', 'ocr')
        
        # Calculer score de complétude
        complete_data['completeness_score'] = self.calculate_completeness(complete_data)
        
        return complete_data

    def extract_from_cv_image(self, image_url, player_name):
        """Extraction OCR depuis l'image CV"""
        try:
            # Construire URL complète
            if image_url.startswith('/'):
                full_url = f"http://www.ffvb.org{image_url}"
            else:
                full_url = image_url
            
            # Télécharger image
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            # Traitement OCR optimisé
            image = Image.open(BytesIO(response.content))
            best_text, method = self.get_best_ocr_text(image)
            
            if not best_text:
                print(f"   ⚠️ Aucun texte extrait")
                return None
            
            # Parser le texte pour extraire les données
            extracted_data = self.parse_player_data_from_text(best_text, player_name)
            extracted_data['ocr_method'] = method
            extracted_data['ocr_text_length'] = len(best_text)
            
            return extracted_data
            
        except Exception as e:
            print(f"   ❌ Erreur OCR: {e}")
            return None

    def get_best_ocr_text(self, image):
        """Obtient le meilleur texte OCR possible"""
        # Configurations OCR à tester
        ocr_configs = [
            ('PSM6-ENG', '--psm 6 -l eng'),
            ('PSM4-ENG', '--psm 4 -l eng'),
            ('PSM3-ENG', '--psm 3 -l eng')
        ]
        
        # Préprocessings à tester
        preprocessed_images = self.create_image_variants(image)
        
        best_text = ""
        best_method = "none"
        max_length = 0
        
        # Tester toutes les combinaisons
        for preprocess_name, processed_img in preprocessed_images.items():
            for config_name, config_str in ocr_configs:
                try:
                    text = pytesseract.image_to_string(processed_img, config=config_str)
                    
                    if len(text) > max_length:
                        max_length = len(text)
                        best_text = text
                        best_method = f"{preprocess_name}+{config_name}"
                
                except Exception:
                    continue
        
        return best_text, best_method

    def create_image_variants(self, image):
        """Crée plusieurs versions optimisées de l'image"""
        variants = {}
        
        try:
            # Redimensionner si nécessaire
            if image.size[0] < 1200:
                scale = 1200 / image.size[0]
                new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
                resized = image.resize(new_size, Image.Resampling.LANCZOS)
            else:
                resized = image
            
            variants['Original'] = resized
            
            # Amélioration contraste
            enhancer = ImageEnhance.Contrast(resized)
            variants['Contrast'] = enhancer.enhance(2.0)
            
            # Amélioration netteté
            enhancer = ImageEnhance.Sharpness(resized)
            variants['Sharp'] = enhancer.enhance(2.5)
            
            # Niveaux de gris
            gray = resized.convert('L')
            variants['Gray'] = gray
            
            # OpenCV avancé
            opencv_img = self.opencv_preprocessing(gray)
            if opencv_img:
                variants['OpenCV'] = opencv_img
                
        except Exception as e:
            variants['Original'] = image
        
        return variants

    def opencv_preprocessing(self, pil_image):
        """Préprocessing OpenCV optimisé"""
        try:
            # Convertir PIL vers OpenCV
            opencv_img = np.array(pil_image)
            
            # Débruitage
            denoised = cv2.fastNlMeansDenoising(opencv_img)
            
            # Amélioration contraste adaptatif
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Binarisation adaptative
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return Image.fromarray(binary)
            
        except Exception:
            return None

    def parse_player_data_from_text(self, text, player_name):
        """Parse le texte OCR pour extraire les données du joueur"""
        data = {}
        
        # Nettoyer le texte
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Patterns d'extraction optimisés
        patterns = {
            'poste': [
                r'\b(ATTAQUANT|ATTACKANT|SPIKER)\b',
                r'\b(PASSEUR|SETTER)\b', 
                r'\b(CENTRAL|MIDDLE)\b',
                r'\b(LIBÉRO|LIBERO)\b',
                r'\b(RÉCEPTIONNEUR|RECEPTIONNEUR|OUTSIDE)\b',
                r'\b(POINTU|OPPOSITE)\b'
            ],
            'taille': [
                r'\b(1[789]\d|20\d|21\d)\b(?:\s*cm)?',  # 170-219 cm
                r'\b(\d\.\d{2})\s*m\b'  # Format 1.95m
            ],
            'poids': [
                r'\b([6-9]\d|1[0-2]\d)\b(?:\s*kg)?',  # 60-129 kg
                r'poids[\s:]*(\d{2,3})'
            ],
            'naissance': [
                r'\b(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{4})\b'
            ],
            'club': [
                r'\b(PARIS VOLLEY|MONTPELLIER|TOURS|CHAUMONT|POITIERS|CANNES)\b',
                r'\b(PERUGIA|MODENA|MILANO|LATINA|CIVITANOVA)\b',
                r'\b([A-Z]{2,15}(?:\s+[A-Z]{2,15})*\s+(?:VOLLEY|VB))\b'
            ],
            'selections': [
                r'\b(\d+)\s*(?:sélections?|selections?|caps?)\b'
            ]
        }
        
        # Appliquer les patterns
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    value = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    validated_value = self.validate_extracted_value(field, value, player_name)
                    if validated_value:
                        data[field] = validated_value
                        break
        
        # Calculer l'âge si date de naissance trouvée
        if data.get('naissance'):
            age = self.calculate_age(data['naissance'])
            if age:
                data['age'] = str(age)
        
        return data

    def validate_extracted_value(self, field, value, player_name):
        """Valide une valeur extraite"""
        if field == 'taille':
            if '.' in value:  # Format 1.95m
                try:
                    meters = float(value)
                    cm = int(meters * 100)
                    return str(cm) if 170 <= cm <= 220 else None
                except:
                    return None
            elif value.isdigit():
                cm = int(value)
                return str(cm) if 170 <= cm <= 220 else None
        
        elif field == 'poids':
            if value.isdigit():
                kg = int(value)
                return str(kg) if 60 <= kg <= 130 else None
        
        elif field == 'poste':
            # Normalisation des postes
            poste_map = {
                'attaquant': 'Attaquant', 'attackant': 'Attaquant', 'spiker': 'Attaquant',
                'passeur': 'Passeur', 'setter': 'Passeur',
                'central': 'Central', 'middle': 'Central',
                'libéro': 'Libéro', 'libero': 'Libéro',
                'réceptionneur': 'Réceptionneur-Attaquant', 'receptionneur': 'Réceptionneur-Attaquant',
                'outside': 'Réceptionneur-Attaquant', 'pointu': 'Attaquant (Pointu)', 'opposite': 'Attaquant (Pointu)'
            }
            return poste_map.get(value.lower(), value.title())
        
        elif field == 'selections':
            if value.isdigit():
                sel = int(value)
                return str(sel) if 0 <= sel <= 500 else None
        
        elif field == 'club':
            return value.title() if 3 <= len(value) <= 30 else None
        
        elif field == 'naissance':
            # Valider format date
            if re.match(r'\d{1,2}[/\.-]\d{1,2}[/\.-]\d{4}', value):
                return value
        
        return value

    def calculate_age(self, birth_date):
        """Calcule l'âge depuis la date de naissance"""
        try:
            parts = re.split(r'[/\.-]', birth_date)
            if len(parts) == 3:
                year = int(parts[2])
                current_year = datetime.now().year
                age = current_year - year
                return age if 16 <= age <= 45 else None
        except:
            pass
        return None

    def calculate_completeness(self, player_data):
        """Calcule le pourcentage de complétude des données"""
        important_fields = ['nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age', 'club']
        filled_count = sum(1 for field in important_fields if player_data.get(field, '').strip())
        return round((filled_count / len(important_fields)) * 100, 1)

    def init_final_csv(self):
        """Initialise le fichier CSV final"""
        headers = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age', 'naissance',
            'club', 'selections', 'url_cv_image', 'url_page_principale',
            'completeness_score', 'extraction_success', 'extraction_method',
            'extraction_date'
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        
        print(f"✅ Fichier CSV initialisé: {self.output_file}")

    def save_to_final_csv(self, player_data):
        """Sauvegarde un joueur dans le CSV final"""
        row = [
            player_data.get('nom_joueur', ''),
            player_data.get('numero', ''),
            player_data.get('poste', ''),
            player_data.get('taille', ''),
            player_data.get('poids', ''),
            player_data.get('age', ''),
            player_data.get('naissance', ''),
            player_data.get('club', ''),
            player_data.get('selections', ''),
            player_data.get('url_cv_image', ''),
            player_data.get('url_page_principale', ''),
            player_data.get('completeness_score', 0),
            player_data.get('extraction_success', False),
            player_data.get('extraction_method', ''),
            player_data.get('extraction_date', '')
        ]
        
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def show_extraction_summary(self, player_data):
        """Affiche un résumé de l'extraction pour un joueur"""
        extracted_fields = []
        key_fields = ['poste', 'taille', 'poids', 'age', 'club']
        
        for field in key_fields:
            value = player_data.get(field, '').strip()
            if value:
                extracted_fields.append(f"{field}:{value}")
        
        if extracted_fields:
            print(f"   ✅ Extraits: {', '.join(extracted_fields[:3])}")
        else:
            print(f"   ⚠️ Aucune donnée extraite")
        
        completeness = player_data.get('completeness_score', 0)
        method = player_data.get('extraction_method', 'none')
        print(f"   📊 Complétude: {completeness}% | Méthode: {method}")

    def show_final_summary(self, total_players):
        """Affiche le résumé final de l'extraction"""
        print(f"\n🎉 EXTRACTION TERMINÉE!")
        print("=" * 30)
        print(f"📊 Joueurs traités: {total_players}")
        print(f"✅ Extractions réussies: {self.successful_extractions}")
        print(f"📄 Fichier final: {self.output_file}")
        
        # Analyser le fichier final
        if os.path.exists(self.output_file):
            self.analyze_final_results()

    def analyze_final_results(self):
        """Analyse les résultats finaux"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                results = list(reader)
            
            if results:
                # Complétude moyenne
                scores = [float(r.get('completeness_score', 0)) for r in results]
                avg_completeness = sum(scores) / len(scores)
                
                print(f"\n📈 ANALYSE FINALE:")
                print(f"   Complétude moyenne: {avg_completeness:.1f}%")
                
                # Succès par champ
                fields = ['poste', 'taille', 'poids', 'club']
                for field in fields:
                    count = sum(1 for r in results if r.get(field, '').strip())
                    pct = (count / len(results)) * 100
                    print(f"   {field}: {count}/{len(results)} ({pct:.1f}%)")
                
                # Top 3 joueurs les plus complets
                best = sorted(results, key=lambda x: float(x.get('completeness_score', 0)), reverse=True)[:3]
                print(f"\n🏆 TOP 3 EXTRACTIONS:")
                for i, player in enumerate(best, 1):
                    name = player.get('nom_joueur', 'N/A')
                    score = player.get('completeness_score', 0)
                    poste = player.get('poste', 'N/A')
                    print(f"   {i}. {name} ({poste}) - {score}%")
        
        except Exception as e:
            print(f"⚠️ Erreur analyse: {e}")

def main():
    """Fonction principale"""
    print("🏐 EXTRACTEUR FINAL FFVB")
    print("Génération du fichier CSV complet")
    print()
    
    try:
        extractor = FFVBFinalExtractor()
        extractor.run_complete_extraction()
        
        print(f"\n🎯 MISSION ACCOMPLIE!")
        print(f"📋 Votre fichier CSV complet: {extractor.output_file}")
        print(f"📊 Prêt à être utilisé pour vos analyses!")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()