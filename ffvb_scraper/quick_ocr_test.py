# quick_ocr_test.py
"""
Test rapide pour vérifier l'extraction OCR sur quelques joueurs
et optimiser les patterns avant le traitement complet
"""

import requests
import re
from urllib.parse import unquote

# Import OCR conditionnel
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def test_single_player_ocr(player_name, image_url):
    """Teste l'extraction OCR sur un seul joueur"""
    print(f"\n🏐 TEST OCR: {player_name}")
    print("-" * 40)
    
    try:
        # Construire URL complète
        if image_url.startswith('/'):
            full_url = f"http://www.ffvb.org{image_url}"
        else:
            full_url = image_url
        
        print(f"📥 Téléchargement: {full_url}")
        
        # Télécharger image
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        
        if not OCR_AVAILABLE:
            print("⚠️ OCR non disponible - analyse de l'URL uniquement")
            analyze_filename_only(image_url)
            return
        
        # Traitement OCR
        from io import BytesIO
        image = Image.open(BytesIO(response.content))
        
        print(f"🖼️ Image: {image.size[0]}x{image.size[1]} pixels")
        
        # OCR de base
        text = pytesseract.image_to_string(image, config='--psm 6 -l fra')
        
        if not text.strip():
            print("❌ Aucun texte détecté")
            return
        
        print(f"✅ OCR réussi - {len(text)} caractères")
        
        # Analyser le contenu
        analyze_ocr_content(text)
        
        # Tester les patterns d'extraction
        test_extraction_patterns(text)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def analyze_filename_only(image_url):
    """Analyse uniquement le nom de fichier"""
    try:
        decoded_url = unquote(image_url)
        print(f"📁 URL décodée: {decoded_url}")
        
        # Extraire info depuis le nom de fichier
        match = re.search(r'CV\s+JOUEURS/(\d+)\s+([^/]+?)\.png', decoded_url, re.IGNORECASE)
        
        if match:
            numero = match.group(1)
            nom = match.group(2).strip()
            print(f"📋 Depuis filename - Numéro: {numero}, Nom: {nom}")
        else:
            print("⚠️ Pattern filename non reconnu")
    
    except Exception as e:
        print(f"❌ Erreur analyse filename: {e}")

def analyze_ocr_content(text):
    """Analyse le contenu OCR brut"""
    print(f"\n📄 CONTENU OCR (premiers 500 caractères):")
    print("-" * 50)
    print(text[:500])
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Longueur totale: {len(text)} caractères")
    print(f"   Lignes: {len(text.split('\n'))}")
    print(f"   Mots: {len(text.split())}")
    
    # Détecter la langue/structure
    french_indicators = ['poste', 'taille', 'poids', 'âge', 'club', 'sélections']
    french_count = sum(1 for indicator in french_indicators if indicator in text.lower())
    print(f"   Indicateurs français: {french_count}/{len(french_indicators)}")

def test_extraction_patterns(text):
    """Teste les patterns d'extraction sur le texte"""
    print(f"\n🔍 TEST DES PATTERNS D'EXTRACTION:")
    print("-" * 40)
    
    patterns = {
        'Poste': [
            r'(?:poste|position)[\s:]*([^,\n\r\.]+)',
            r'(attaquant|passeur|central|libéro|libero|réceptionneur|pointu|opposite)'
        ],
        'Taille': [
            r'(?:taille|height)[\s:]*(\d{1,3})(?:\s*cm)?',
            r'(\d{3})\s*cm',
            r'(\d\.\d{2})\s*m'
        ],
        'Poids': [
            r'(?:poids|weight)[\s:]*(\d{2,3})(?:\s*kg)?',
            r'(\d{2,3})\s*kg'
        ],
        'Âge': [
            r'(?:âge|age)[\s:]*(\d{1,2})(?:\s*ans?)?',
            r'(\d{1,2})\s*ans?'
        ],
        'Club': [
            r'(?:club|équipe)[\s:]+([^,\n\r\.]+)'
        ]
    }
    
    found_data = {}
    
    for field_name, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                found_data[field_name] = value
                print(f"   ✅ {field_name}: {value}")
                break
        else:
            print(f"   ❌ {field_name}: Non trouvé")
    
    return found_data

def test_multiple_players():
    """Teste plusieurs joueurs pour validation"""
    # Joueurs de test (depuis vos données extraites)
    test_players = [
        ("Kevin Tillie", "/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/7%20Kevin%20Tillie.png"),
        ("Trevor Clevenot", "/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/17%20Trevor%20Clevenot.png"),
        ("Théo Faure", "/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/21%20Th%C3%A9o%20Faure.png")
    ]
    
    print("🧪 TEST MULTI-JOUEURS")
    print("=" * 30)
    
    results = []
    
    for name, url in test_players:
        try:
            print(f"\n{'='*50}")
            result = test_single_player_ocr(name, url)
            results.append(result)
            
        except Exception as e:
            print(f"❌ Erreur pour {name}: {e}")
    
    # Résumé des tests
    print(f"\n📊 RÉSUMÉ DES TESTS")
    print("=" * 30)
    print(f"Joueurs testés: {len(test_players)}")
    
    if OCR_AVAILABLE:
        print("✅ OCR disponible et testé")
    else:
        print("⚠️ OCR non disponible - tests limités")

def interactive_test():
    """Test interactif pour un joueur spécifique"""
    print("\n🎯 TEST INTERACTIF")
    print("=" * 20)
    
    # Demander à l'utilisateur
    name = input("Nom du joueur: ").strip()
    url = input("URL de l'image CV: ").strip()
    
    if name and url:
        test_single_player_ocr(name, url)
    else:
        print("❌ Nom ou URL manquant")

def test_from_csv():
    """Teste depuis le fichier CSV existant"""
    import csv
    import os
    
    csv_file = 'ffvb_players_complete.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ Fichier {csv_file} non trouvé")
        return
    
    print("📋 TEST DEPUIS CSV EXISTANT")
    print("=" * 30)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        print(f"📊 {len(players)} joueurs disponibles")
        
        # Tester les 3 premiers avec images CV
        tested_count = 0
        for player in players:
            if player.get('url_cv_image') and tested_count < 3:
                test_single_player_ocr(
                    player.get('nom_joueur', 'N/A'),
                    player.get('url_cv_image', '')
                )
                tested_count += 1
        
        print(f"\n✅ {tested_count} joueurs testés")
    
    except Exception as e:
        print(f"❌ Erreur lecture CSV: {e}")

def optimize_ocr_settings():
    """Teste différents paramètres OCR pour optimisation"""
    if not OCR_AVAILABLE:
        print("❌ OCR non disponible pour les tests d'optimisation")
        return
    
    print("\n⚙️ OPTIMISATION DES PARAMÈTRES OCR")
    print("=" * 40)
    
    # URL de test
    test_url = "/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/7%20Kevin%20Tillie.png"
    full_url = f"http://www.ffvb.org{test_url}"
    
    try:
        import requests
        from io import BytesIO
        
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        
        # Tester différents configs OCR
        configs = [
            '--psm 6 -l fra',
            '--psm 4 -l fra', 
            '--psm 3 -l fra',
            '--psm 6 -l fra+eng',
            '--psm 6 -l fra --oem 3'
        ]
        
        print("🧪 Test de différentes configurations OCR:")
        
        for i, config in enumerate(configs, 1):
            try:
                text = pytesseract.image_to_string(image, config=config)
                word_count = len(text.split())
                char_count = len(text.strip())
                
                print(f"\n   Config {i}: {config}")
                print(f"   Résultat: {char_count} chars, {word_count} mots")
                
                # Compter les mots français détectés
                french_words = ['poste', 'taille', 'poids', 'club', 'sélection']
                french_found = sum(1 for word in french_words if word in text.lower())
                print(f"   Mots français: {french_found}/{len(french_words)}")
                
            except Exception as e:
                print(f"   ❌ Config {i} échouée: {e}")
    
    except Exception as e:
        print(f"❌ Erreur test optimisation: {e}")

def main():
    """Menu principal"""
    print("🔍 TEST RAPIDE OCR - JOUEURS FFVB")
    print("=" * 35)
    
    if not OCR_AVAILABLE:
        print("⚠️ TESSERACT OCR NON DISPONIBLE")
        print("📦 Installation requise:")
        print("   pip install pytesseract pillow opencv-python")
        print("   + Tesseract système (https://github.com/tesseract-ocr/tesseract)")
        print()
    
    print("📋 MODES DE TEST DISPONIBLES:")
    print("1. 🧪 Test multi-joueurs (Kevin, Trevor, Théo)")
    print("2. 📋 Test depuis CSV existant") 
    print("3. 🎯 Test interactif (joueur spécifique)")
    print("4. ⚙️ Optimisation paramètres OCR")
    print("5. 🔍 Test analyse filename uniquement")
    
    try:
        choice = input("\nChoisissez un mode (1-5): ").strip()
        
        if choice == "1":
            test_multiple_players()
        
        elif choice == "2":
            test_from_csv()
        
        elif choice == "3":
            interactive_test()
        
        elif choice == "4":
            optimize_ocr_settings()
        
        elif choice == "5":
            # Test analyse filename
            test_url = "/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/7%20Kevin%20Tillie.png"
            analyze_filename_only(test_url)
        
        else:
            print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

def quick_validation():
    """Validation rapide pour voir si OCR fonctionne"""
    if not OCR_AVAILABLE:
        print("❌ OCR non disponible")
        return False
    
    try:
        # Test basique
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"❌ Erreur Tesseract: {e}")
        return False

if __name__ == "__main__":
    # Validation rapide
    print("🔧 VÉRIFICATION DES DÉPENDANCES...")
    ocr_ok = quick_validation()
    
    if ocr_ok:
        print("✅ Toutes les dépendances OK")
    else:
        print("⚠️ OCR limité ou non disponible")
    
    print()
    main()