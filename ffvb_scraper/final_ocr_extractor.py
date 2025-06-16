# final_ocr_extractor_optimized.py
"""
Extracteur OCR optimisé pour les joueurs FFVB
Version améliorée avec meilleurs patterns et préprocessing
"""

import csv
import json
import os
import requests
import re
import time
import cv2
import numpy as np
from datetime import datetime
from io import BytesIO

# Configuration OCR validée
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# Configuration Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class FFVBOptimizedExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.output_file = 'ffvb_joueurs_donnees_optimisees.csv'
        self.success_count = 0
        self.error_count = 0
        self.extracted_data = []
        self.debug_mode = True  # Pour voir les patterns qui matchent
        
        # Patterns d'extraction perfectionnés
        self.patterns = {
            'poste': [
                # Patterns français directs
                r'(?:^|\s)(ATTAQUANT|ATTACKANT)(?:\s|$)',
                r'(?:^|\s)(PASSEUR)(?:\s|$)',
                r'(?:^|\s)(CENTRAL|CENTRAUX)(?:\s|$)',
                r'(?:^|\s)(LIBÉRO|LIBERO)(?:\s|$)', 
                r'(?:^|\s)(RÉCEPTIONNEUR|RECEPTIONNEUR)(?:\s|$)',
                r'(?:^|\s)(POINTU|OPPOSITE)(?:\s|$)',
                # Patterns contextuels
                r'poste[\s:]*([A-Za-z\s]{3,20})',
                r'position[\s:]*([A-Za-z\s]{3,20})',
                # Patterns anglais
                r'(?:^|\s)(SPIKER|ATTACKER)(?:\s|$)',
                r'(?:^|\s)(SETTER)(?:\s|$)',
                r'(?:^|\s)(MIDDLE)(?:\s|$)',
                r'(?:^|\s)(OUTSIDE)(?:\s|$)'
            ],
            'taille': [
                # Patterns précis pour la taille
                r'(?:taille|height)[\s:]*(\d{3})(?:\s*cm)?',
                r'(\d{3})\s*cm(?:\s|$)',
                r'(\d\.\d{2})\s*m(?:\s|$)',
                r'(\d{1,3})\s*centimètres?',
                # Pattern contextuel - recherche 3 chiffres entre 170-220
                r'(?:^|\s)(1[7-9]\d|2[0-1]\d)(?:\s|$)',
                # Dans un contexte de mensurations
                r'(?:mensurations?|physique)[\s\S]{0,50}(\d{3})'
            ],
            'poids': [
                # Patterns précis pour le poids
                r'(?:poids|weight|masse)[\s:]*(\d{2,3})(?:\s*kg)?',
                r'(\d{2,3})\s*kg(?:\s|$)',
                r'(\d{2,3})\s*kilos?(?:\s|$)',
                # Pattern contextuel - recherche 2-3 chiffres entre 60-130
                r'(?:^|\s)([6-9]\d|1[0-2]\d|130)(?:\s*kg|\s|$)'
            ],
            'naissance': [
                # Formats de date variés
                r'(?:naissance|né|birth|born)[\s:]*(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{4})',
                r'(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{4})',
                r'(\d{4}[/\.-]\d{1,2}[/\.-]\d{1,2})',
                # Format texte
                r'(\d{1,2}\s+\w+\s+\d{4})'
            ],
            'club': [
                # Patterns pour clubs français courants
                r'(?:club|équipe|team)[\s:]*([A-Z][A-Za-z\s]{2,30})',
                # Clubs spécifiques connus
                r'(PARIS VOLLEY|MONTPELLIER|TOURS|POITIERS|NANTES|CHAUMONT|CANNES|AJACCIO)',
                r'(CUCINE LUBE|PERUGIA|MODENA|MILANO|RAVENNA|CIVITANOVA)',
                r'(ZAKSA|RESOVIA|BERLIN|FRIEDRICHSHAFEN|KAZAN)',
                # Pattern général clubs
                r'(?:^|\s)([A-Z]{2,}(?:\s+[A-Z]{2,})*\s+(?:VOLLEY|VOLLEYBALL|VB))(?:\s|$)',
                r'(?:^|\s)(AS|AC|US|USC|VB|VOLLEY)\s+([A-Z][A-Za-z\s]{2,20})(?:\s|$)'
            ],
            'selections': [
                r'(?:sélections?|selections?|caps?)[\s:]*(\d+)',
                r'(\d+)\s*sélections?(?:\s|$)',
                r'(\d+)\s*caps?(?:\s|$)',
                r'équipe de france[\s\S]{0,50}(\d+)'
            ],
            'numero_maillot': [
                r'(?:n°|#|numéro|number)[\s:]*(\d{1,2})',
                r'maillot[\s:]*(\d{1,2})',
                # En début de texte souvent
                r'^[\s\S]{0,30}(\d{1,2})(?:\s|$)'
            ]
        }
        
        # Configurations OCR multiples pour tester
        self.ocr_configs = [
            ('Standard', '--psm 6 -l eng'),
            ('Précis', '--psm 8 -l eng'),
            ('Layout', '--psm 4 -l eng'),
            ('Sparse', '--psm 3 -l eng'),
            ('Single block', '--psm 7 -l eng')
        ]

    def extract_all_players(self):
        """Extrait les données de tous les joueurs avec optimisations"""
        print("🏐 EXTRACTION OCR OPTIMISÉE - JOUEURS FFVB")
        print("=" * 50)
        
        # Charger les joueurs
        players = self.load_players_from_csv()
        if not players:
            print("❌ Aucun joueur trouvé")
            return
        
        print(f"📊 {len(players)} joueurs à traiter")
        print(f"🔧 Configurations OCR multiples")
        print(f"🎯 Patterns optimisés pour postes/clubs français")
        print()
        
        # Initialiser le fichier de sortie
        self.init_output_file()
        
        # Traiter chaque joueur avec debug
        for i, player in enumerate(players, 1):
            name = player.get('nom_joueur', 'N/A')
            numero = player.get('numero', 'N/A')
            
            print(f"🏐 [{i:2d}/{len(players)}] {name} (#{numero})")
            
            try:
                # Extraire avec toutes les optimisations
                ocr_data = self.extract_player_optimized(player, name)
                
                # Combiner et enrichir
                complete_data = self.combine_player_data(player, ocr_data)
                
                # Sauvegarder
                self.save_player_data(complete_data)
                self.extracted_data.append(complete_data)
                
                self.success_count += 1
                
                # Afficher résumé détaillé
                self.print_detailed_summary(complete_data, name)
                
                # Pause respectueuse
                time.sleep(1.5)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                self.error_count += 1
                self.save_player_data(player)
        
        # Résumé final avec analyses
        self.print_comprehensive_summary(len(players))

    def extract_player_optimized(self, player, player_name):
        """Extraction OCR optimisée pour un joueur"""
        image_url = player.get('url_cv_image', '')
        if not image_url:
            return {}
        
        try:
            # Télécharger l'image
            if image_url.startswith('/'):
                full_url = f"http://www.ffvb.org{image_url}"
            else:
                full_url = image_url
            
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            original_image = Image.open(BytesIO(response.content))
            
            # Tester plusieurs préprocessings et configs OCR
            best_result = self.test_multiple_ocr_approaches(original_image, player_name)
            
            return best_result
        
        except Exception as e:
            print(f"   ❌ Extraction échouée: {e}")
            return {'ocr_status': 'error', 'ocr_error': str(e)}

    def test_multiple_ocr_approaches(self, image, player_name):
        """Teste plusieurs approches OCR et garde la meilleure"""
        
        # Différents préprocessings
        preprocessed_images = self.create_preprocessed_versions(image)
        
        all_results = []
        
        # Tester chaque combinaison preprocessing + config OCR
        for preprocess_name, processed_image in preprocessed_images.items():
            for config_name, config_str in self.ocr_configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config_str)
                    
                    if text.strip():
                        # Parser ce texte
                        parsed_data = self.parse_ocr_text_advanced(text, player_name)
                        parsed_data['ocr_method'] = f"{preprocess_name}+{config_name}"
                        parsed_data['ocr_text_length'] = len(text)
                        parsed_data['raw_text_sample'] = text[:200]
                        
                        # Calculer un score de qualité
                        quality_score = self.calculate_extraction_quality(parsed_data, player_name)
                        parsed_data['quality_score'] = quality_score
                        
                        all_results.append(parsed_data)
                        
                        if self.debug_mode and quality_score > 3:
                            print(f"   🔍 {preprocess_name}+{config_name}: Score {quality_score}")
                
                except Exception as e:
                    continue
        
        # Retourner le meilleur résultat
        if all_results:
            best = max(all_results, key=lambda x: x.get('quality_score', 0))
            best['ocr_status'] = 'success'
            
            if self.debug_mode:
                print(f"   🏆 Meilleur: {best.get('ocr_method')} (score: {best.get('quality_score')})")
            
            return best
        else:
            return {'ocr_status': 'no_text'}

    def create_preprocessed_versions(self, image):
        """Crée plusieurs versions préprocessées de l'image"""
        versions = {}
        
        try:
            # 1. Image originale redimensionnée
            if image.size[0] < 1200:
                scale_factor = 1200 / image.size[0]
                new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
                resized = image.resize(new_size, Image.Resampling.LANCZOS)
            else:
                resized = image
            
            versions['original'] = resized
            
            # 2. Amélioration contraste
            enhancer = ImageEnhance.Contrast(resized)
            versions['contrast'] = enhancer.enhance(1.8)
            
            # 3. Amélioration netteté
            enhancer = ImageEnhance.Sharpness(resized)
            versions['sharp'] = enhancer.enhance(2.0)
            
            # 4. Niveaux de gris optimisé
            gray = resized.convert('L')
            versions['grayscale'] = gray
            
            # 5. Préprocessing OpenCV avancé
            if gray:
                opencv_version = self.opencv_preprocessing(gray)
                if opencv_version:
                    versions['opencv'] = opencv_version
            
            # 6. Binarisation
            threshold = gray.point(lambda x: 0 if x < 128 else 255, '1')
            versions['binary'] = threshold
            
        except Exception as e:
            print(f"   ⚠️ Erreur preprocessing: {e}")
            versions['original'] = image
        
        return versions

    def opencv_preprocessing(self, pil_image):
        """Préprocessing OpenCV avancé"""
        try:
            # Convertir PIL en OpenCV
            open_cv_image = np.array(pil_image)
            
            # Débruitage
            denoised = cv2.fastNlMeansDenoising(open_cv_image)
            
            # Amélioration contraste adaptatif
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Binarisation adaptative
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Reconvertir en PIL
            return Image.fromarray(binary)
            
        except Exception as e:
            return None

    def parse_ocr_text_advanced(self, text, player_name):
        """Parsing OCR avancé avec contexte du nom du joueur"""
        data = {}
        
        # Nettoyer et normaliser le texte
        text = self.clean_ocr_text(text)
        
        # Parser avec patterns avancés
        for field, patterns in self.patterns.items():
            field_value = self.extract_field_with_validation(field, patterns, text, player_name)
            if field_value:
                data[field] = field_value
                if self.debug_mode:
                    print(f"     ✅ {field}: {field_value}")
        
        # Post-traitement spécialisé par joueur
        data = self.post_process_by_player_context(data, text, player_name)
        
        return data

    def clean_ocr_text(self, text):
        """Nettoie le texte OCR"""
        # Remplacer caractères mal reconnus courants
        replacements = {
            '|': 'I',
            '0': 'O',  # Dans certains contextes
            '5': 'S',  # Dans certains contextes
            '1': 'I',  # Dans certains contextes
        }
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer caractères parasites
        text = re.sub(r'[^\w\s/\.-:°#]', ' ', text)
        
        return text.strip()

    def extract_field_with_validation(self, field, patterns, text, player_name):
        """Extrait un champ avec validation contextuelle"""
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        value = match[-1] if match[-1] else match[0]
                    else:
                        value = match
                    
                    # Validation spécifique par champ
                    validated_value = self.validate_field_value(field, value, text, player_name)
                    
                    if validated_value:
                        return validated_value
        
        return None

    def validate_field_value(self, field, value, full_text, player_name):
        """Valide une valeur extraite selon le champ"""
        
        value = value.strip()
        
        if field == 'taille':
            # Validation taille
            if value.replace('.', '').isdigit():
                if '.' in value:  # Format 1.95m
                    try:
                        meters = float(value)
                        cm_value = int(meters * 100)
                        if 170 <= cm_value <= 220:
                            return str(cm_value)
                    except:
                        pass
                else:  # Format 195cm
                    taille = int(value)
                    if 170 <= taille <= 220:
                        return str(taille)
        
        elif field == 'poids':
            if value.isdigit():
                poids = int(value)
                if 60 <= poids <= 130:
                    return str(poids)
        
        elif field == 'poste':
            # Normalisation postes avec validation contextuelle
            poste_mapping = {
                'attaquant': 'Attaquant',
                'attackant': 'Attaquant',
                'spiker': 'Attaquant',
                'attacker': 'Attaquant',
                'pointu': 'Attaquant (Pointu)',
                'opposite': 'Attaquant (Pointu)',
                'passeur': 'Passeur',
                'setter': 'Passeur',
                'central': 'Central',
                'centraux': 'Central',
                'middle': 'Central',
                'libéro': 'Libéro',
                'libero': 'Libéro',
                'réceptionneur': 'Réceptionneur-Attaquant',
                'receptionneur': 'Réceptionneur-Attaquant',
                'outside': 'Réceptionneur-Attaquant'
            }
            
            value_lower = value.lower()
            for key, mapped in poste_mapping.items():
                if key in value_lower:
                    return mapped
            
            # Si rien trouvé mais contient des mots-clés volley
            if any(word in value_lower for word in ['volley', 'ball', 'sport']):
                return None  # Probablement pas un poste
            
            return value.title() if len(value) < 20 else None
        
        elif field == 'club':
            # Validation clubs
            if len(value) < 3 or len(value) > 30:
                return None
            
            # Exclure certains mots qui ne sont pas des clubs
            excluded_words = ['volley', 'ball', 'sport', 'france', 'équipe', 'team']
            if value.lower() in excluded_words:
                return None
            
            # Nettoyer et formater
            club = re.sub(r'\s+', ' ', value).strip().title()
            
            # Vérifications spéciales pour clubs connus
            known_clubs = ['Paris Volley', 'Montpellier', 'Tours VB', 'Poitiers', 'Chaumont']
            for known in known_clubs:
                if known.lower() in club.lower():
                    return known
            
            return club
        
        elif field == 'selections':
            if value.isdigit():
                sel = int(value)
                if 0 <= sel <= 500:  # Nombre réaliste de sélections
                    return str(sel)
        
        elif field == 'naissance':
            # Validation format date
            if re.match(r'\d{1,2}[/\.-]\d{1,2}[/\.-]\d{4}', value):
                return value
        
        elif field == 'numero_maillot':
            if value.isdigit():
                num = int(value)
                if 1 <= num <= 99:
                    return str(num)
        
        return value if value else None

    def post_process_by_player_context(self, data, text, player_name):
        """Post-traitement basé sur le contexte du joueur"""
        
        # Corrections spécifiques pour certains joueurs connus
        player_corrections = {
            'Théo Faure': {
                'poste_hints': ['réceptionneur', 'attaquant'],
                'club_hints': ['tours', 'chaumont'],
                'taille_range': (185, 200)
            },
            'Kevin Tillie': {
                'poste_hints': ['attaquant', 'pointu'],
                'club_hints': ['paris', 'latina'],
                'taille_range': (195, 205)
            },
            'Trevor Clevenot': {
                'poste_hints': ['réceptionneur', 'attaquant'],
                'club_hints': ['perugia', 'modena'],
                'taille_range': (190, 200)
            }
        }
        
        if player_name in player_corrections:
            corrections = player_corrections[player_name]
            
            # Correction du poste si manquant
            if not data.get('poste'):
                for hint in corrections['poste_hints']:
                    if hint in text.lower():
                        data['poste'] = hint.title()
                        break
            
            # Validation de la taille
            if data.get('taille'):
                try:
                    taille = int(data['taille'])
                    min_t, max_t = corrections['taille_range']
                    if not (min_t <= taille <= max_t):
                        # Chercher une autre taille dans le texte
                        other_heights = re.findall(r'(\d{3})', text)
                        for height in other_heights:
                            h = int(height)
                            if min_t <= h <= max_t:
                                data['taille'] = height
                                break
                except:
                    pass
        
        return data

    def calculate_extraction_quality(self, data, player_name):
        """Calcule un score de qualité de l'extraction"""
        score = 0
        
        # Points pour chaque champ trouvé
        field_points = {
            'poste': 3,      # Très important
            'taille': 2,     # Important
            'poids': 2,      # Important
            'club': 2,       # Important
            'naissance': 1,  # Utile
            'selections': 1, # Utile
            'numero_maillot': 1
        }
        
        for field, points in field_points.items():
            if data.get(field):
                score += points
        
        # Bonus pour cohérence des données
        if data.get('taille') and data.get('poids'):
            try:
                taille = int(data['taille'])
                poids = int(data['poids'])
                # Vérifier cohérence taille/poids
                if 170 <= taille <= 220 and 60 <= poids <= 130:
                    score += 1
            except:
                pass
        
        # Bonus pour texte long (plus de chances d'avoir trouvé les bonnes infos)
        text_length = data.get('ocr_text_length', 0)
        if text_length > 1000:
            score += 1
        
        return score

    def load_players_from_csv(self):
        """Charge les joueurs depuis le CSV nettoyé ou original"""
        csv_files = ['ffvb_players_clean.csv', 'ffvb_players_complete.csv']
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        players = [row for row in reader if row.get('nom_joueur')]
                    
                    print(f"📂 Fichier utilisé: {csv_file}")
                    return players
                    
                except Exception as e:
                    print(f"⚠️ Erreur lecture {csv_file}: {e}")
                    continue
        
        print(f"❌ Aucun fichier de données trouvé")
        return []

    def combine_player_data(self, original_data, ocr_data):
        """Combine intelligemment les données"""
        combined = original_data.copy()
        
        # Priorité aux données OCR si elles semblent meilleures
        priority_fields = ['poste', 'taille', 'poids', 'age', 'club', 'naissance']
        
        for field in priority_fields:
            ocr_value = ocr_data.get(field)
            original_value = combined.get(field)
            
            if ocr_value and (not original_value or len(str(ocr_value)) > len(str(original_value))):
                combined[field] = ocr_value
        
        # Ajouter métadonnées OCR
        combined['ocr_method'] = ocr_data.get('ocr_method', '')
        combined['quality_score'] = ocr_data.get('quality_score', 0)
        combined['ocr_status'] = ocr_data.get('ocr_status', '')
        
        # Score de complétude
        important_fields = ['nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age']
        filled_count = sum(1 for field in important_fields if combined.get(field))
        combined['completeness_score'] = round((filled_count / len(important_fields)) * 100, 1)
        
        combined['extraction_date'] = datetime.now().isoformat()
        
        return combined

    def init_output_file(self):
        """Initialise le fichier de sortie optimisé"""
        headers = [
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age', 
            'naissance', 'club', 'selections', 'numero_maillot',
            'url_cv_image', 'completeness_score', 'quality_score',
            'ocr_method', 'ocr_status', 'extraction_date'
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def save_player_data(self, data):
        """Sauvegarde optimisée"""
        row = [
            data.get('nom_joueur', ''),
            data.get('numero', ''),
            data.get('poste', ''),
            data.get('taille', ''),
            data.get('poids', ''),
            data.get('age', ''),
            data.get('naissance', ''),
            data.get('club', ''),
            data.get('selections', ''),
            data.get('numero_maillot', ''),
            data.get('url_cv_image', ''),
            data.get('completeness_score', 0),
            data.get('quality_score', 0),
            data.get('ocr_method', ''),
            data.get('ocr_status', ''),
            data.get('extraction_date', '')
        ]
        
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def print_detailed_summary(self, data, player_name):
        """Affiche un résumé détaillé par joueur"""
        found_fields = []
        
        key_fields = ['poste', 'taille', 'poids', 'age', 'club', 'naissance']
        for field in key_fields:
            value = data.get(field)
            if value:
                found_fields.append(f"{field}:{value}")
        
        if found_fields:
            print(f"   ✅ {len(found_fields)} champs: {', '.join(found_fields[:4])}")
        else:
            print(f"   ⚠️ Aucune donnée extraite")
        
        # Afficher méthode et score
        method = data.get('ocr_method', 'N/A')
        quality = data.get('quality_score', 0)
        completeness = data.get('completeness_score', 0)
        
        print(f"   📊 Méthode: {method} | Qualité: {quality} | Complétude: {completeness}%")

    def print_comprehensive_summary(self, total_players):
        """Résumé complet avec analyses"""
        print(f"\n🎉 EXTRACTION OPTIMISÉE TERMINÉE!")
        print("=" * 50)
        print(f"📊 Joueurs traités: {total_players}")
        print(f"✅ Succès: {self.success_count}")
        print(f"❌ Erreurs: {self.error_count}")
        print(f"📄 Fichier: {self.output_file}")
        
        if self.extracted_data:
            # Analyses statistiques
            self.analyze_extraction_results()

    def analyze_extraction_results(self):
        """Analyse les résultats d'extraction"""
        print(f"\n📈 ANALYSES DES RÉSULTATS:")
        print("-" * 30)
        
        # Complétude moyenne
        scores = [float(p.get('completeness_score', 0)) for p in self.extracted_data]
        avg_completeness = sum(scores) / len(scores) if scores else 0
        print(f"📊 Complétude moyenne: {avg_completeness:.1f}%")
        
        # Succès par champ
        fields = ['poste', 'taille', 'poids', 'club']
        for field in fields:
            count = sum(1 for p in self.extracted_data if p.get(field))
            percentage = (count / len(self.extracted_data)) * 100
            print(f"   {field}: {count}/{len(self.extracted_data)} ({percentage:.1f}%)")
        
        # Meilleures méthodes OCR
        methods = {}
        for p in self.extracted_data:
            method = p.get('ocr_method', 'unknown')
            if method not in methods:
                methods[method] = []
            methods[method].append(float(p.get('quality_score', 0)))
        
        print(f"\n🏆 MEILLEURES MÉTHODES OCR:")
        for method, scores in methods.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                print(f"   {method}: {avg_score:.1f} (utilisée {len(scores)} fois)")
        
        # Top joueurs extraits
        best_players = sorted(self.extracted_data, 
                            key=lambda x: float(x.get('completeness_score', 0)), 
                            reverse=True)[:5]
        
        print(f"\n🥇 TOP 5 EXTRACTIONS RÉUSSIES:")
        for i, player in enumerate(best_players, 1):
            name = player.get('nom_joueur', 'N/A')
            poste = player.get('poste', 'N/A')
            taille = player.get('taille', 'N/A')
            club = player.get('club', 'N/A')
            score = player.get('completeness_score', 0)
            print(f"   {i}. {name} - {poste}, {taille}cm, {club} ({score}%)")

def main():
    """Fonction principale optimisée"""
    print("🏐 EXTRACTEUR OCR OPTIMISÉ FFVB")
    print("Version perfectionnée avec patterns améliorés")
    print()
    
    # Options de debug
    debug_choice = input("Mode debug détaillé? (o/n): ").strip().lower()
    
    try:
        extractor = FFVBOptimizedExtractor()
        extractor.debug_mode = (debug_choice == 'o')
        
        if extractor.debug_mode:
            print("🔍 Mode debug activé - affichage détaillé des patterns")
        
        extractor.extract_all_players()
        
        print(f"\n🎯 EXTRACTION OPTIMISÉE TERMINÉE!")
        print(f"📋 Résultats dans: {extractor.output_file}")
        print(f"🔧 Patterns spécialement optimisés pour Théo Faure et autres")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()