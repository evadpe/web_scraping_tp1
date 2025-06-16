# fix_tesseract_language.py
"""
Corrige le problème de pack de langue Tesseract et teste avec anglais
"""

import os
import sys
import requests
from pathlib import Path

def fix_tesseract_language():
    """Corrige les packs de langue Tesseract"""
    print("🔧 CORRECTION PACKS LANGUE TESSERACT")
    print("=" * 40)
    
    try:
        import pytesseract
        from PIL import Image
        from io import BytesIO
        
        # Configuration du chemin Tesseract
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        print(f"✅ Tesseract configuré: {tesseract_path}")
        
        # 1. Tester d'abord avec l'anglais (installé par défaut)
        print(f"\n🧪 Test OCR avec anglais...")
        
        # Télécharger image test
        image_url = "http://www.ffvb.org/data/Files/2025%20-%20EDF%20MASCULINE%20VOLLEY/CV%20JOUEURS/7%20Kevin%20Tillie.png"
        response = requests.get(image_url, timeout=15)
        image = Image.open(BytesIO(response.content))
        
        # Test OCR anglais
        try:
            text_eng = pytesseract.image_to_string(image, config='--psm 6 -l eng')
            print(f"✅ OCR anglais: {len(text_eng)} caractères")
            
            if text_eng.strip():
                print(f"📄 Aperçu texte anglais:")
                print(text_eng[:200])
                print("..." if len(text_eng) > 200 else "")
                
                # Analyser avec patterns anglais/universels
                analyze_extracted_text(text_eng, "anglais")
            
        except Exception as e:
            print(f"❌ Erreur OCR anglais: {e}")
            return False
        
        # 2. Vérifier les langues disponibles
        print(f"\n🔍 Langues Tesseract disponibles:")
        try:
            langs = pytesseract.get_languages()
            print(f"   Langues trouvées: {', '.join(langs)}")
            
            if 'fra' in langs:
                print(f"✅ Français disponible")
                # Tester avec français
                text_fra = pytesseract.image_to_string(image, config='--psm 6 -l fra')
                print(f"✅ OCR français: {len(text_fra)} caractères")
                analyze_extracted_text(text_fra, "français")
            else:
                print(f"❌ Français non disponible")
                install_french_pack()
        
        except Exception as e:
            print(f"⚠️ Erreur vérification langues: {e}")
        
        # 3. Test avec configuration optimisée
        print(f"\n⚙️ Test configuration optimisée...")
        
        # Essayer différentes configurations
        configs = [
            ('PSM 6 Anglais', '--psm 6 -l eng'),
            ('PSM 4 Anglais', '--psm 4 -l eng'),
            ('PSM 3 Anglais', '--psm 3 -l eng'),
        ]
        
        best_result = None
        best_config = None
        best_length = 0
        
        for config_name, config_str in configs:
            try:
                text = pytesseract.image_to_string(image, config=config_str)
                char_count = len(text.strip())
                
                print(f"   {config_name}: {char_count} caractères")
                
                if char_count > best_length:
                    best_length = char_count
                    best_result = text
                    best_config = config_str
            
            except Exception as e:
                print(f"   {config_name}: Erreur - {e}")
        
        if best_result:
            print(f"\n🏆 MEILLEURE CONFIGURATION: {best_config}")
            print(f"📊 Texte extrait: {best_length} caractères")
            
            # Sauvegarder la configuration qui fonctionne
            save_working_config_english(best_config, best_result)
            
            # Analyser le meilleur résultat
            analyze_extracted_text(best_result, "meilleur")
            
            return True
        
        return False
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

def analyze_extracted_text(text, source_name):
    """Analyse le texte extrait pour trouver des informations"""
    print(f"\n🔍 ANALYSE TEXTE ({source_name.upper()}):")
    print("-" * 30)
    
    import re
    
    # Patterns universels (marchent en anglais et français)
    patterns = {
        'Nom Kevin': r'(Kevin)',
        'Nom Tillie': r'(Tillie)',
        'Numéro': r'(\d{1,2})(?:\s|$)',
        'Taille (cm)': r'(\d{3})',  # 3 chiffres = probablement taille
        'Poids (kg)': r'(\d{2,3})(?:\s*kg|\s*kilo)',
        'Âge': r'(\d{2})(?:\s*ans?|\s*years?)',
        'Attaquant': r'(attaquant|attacker|spiker)',
        'Numéro maillot': r'(?:n°|#|number)[\s:]*(\d{1,2})',
        'Club/Team': r'(volley|club|team)[\s:]([A-Za-z\s]{3,20})',
        'Sélections': r'(\d+)(?:\s*sélections?|selections?|caps?)'
    }
    
    found_info = {}
    
    for info_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Prendre la première occurrence
            if isinstance(matches[0], tuple):
                value = matches[0][-1]  # Dernier élément du tuple
            else:
                value = matches[0]
            
            found_info[info_type] = value.strip()
            print(f"✅ {info_type}: {value.strip()}")
    
    if not found_info:
        print(f"❌ Aucune information structurée trouvée")
    else:
        print(f"📊 Total trouvé: {len(found_info)} informations")
    
    return found_info

def install_french_pack():
    """Guide pour installer le pack français"""
    print(f"\n📦 INSTALLATION PACK FRANÇAIS:")
    print("-" * 30)
    
    tessdata_dir = r"C:\Program Files\Tesseract-OCR\tessdata"
    
    print(f"📁 Répertoire tessdata: {tessdata_dir}")
    
    if os.path.exists(tessdata_dir):
        print(f"✅ Répertoire tessdata trouvé")
        
        # Vérifier les fichiers existants
        existing_files = os.listdir(tessdata_dir)
        print(f"📋 Fichiers existants: {len(existing_files)}")
        
        if 'fra.traineddata' in existing_files:
            print(f"✅ fra.traineddata déjà présent")
        else:
            print(f"❌ fra.traineddata manquant")
            print(f"\n💾 SOLUTION:")
            print(f"1. Téléchargez: https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata")
            print(f"2. Copiez le fichier dans: {tessdata_dir}")
            print(f"3. Relancez ce script")
            
            # Tentative de téléchargement automatique
            try_download_french_pack(tessdata_dir)
    else:
        print(f"❌ Répertoire tessdata non trouvé: {tessdata_dir}")

def try_download_french_pack(tessdata_dir):
    """Tente de télécharger automatiquement le pack français"""
    print(f"\n🔄 Tentative téléchargement automatique...")
    
    try:
        fra_url = "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata"
        fra_path = os.path.join(tessdata_dir, "fra.traineddata")
        
        print(f"📥 Téléchargement depuis: {fra_url}")
        
        response = requests.get(fra_url, timeout=30)
        response.raise_for_status()
        
        with open(fra_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Pack français téléchargé: {fra_path}")
        print(f"📊 Taille: {len(response.content):,} bytes")
        
        return True
    
    except Exception as e:
        print(f"❌ Échec téléchargement automatique: {e}")
        print(f"💡 Téléchargement manuel requis")
        return False

def save_working_config_english(best_config, sample_text):
    """Sauvegarde la configuration OCR qui fonctionne"""
    
    config_content = f'''# ocr_config_working.py
"""
Configuration OCR FFVB qui fonctionne - Version Anglais
"""

import pytesseract

# Configuration Tesseract
TESSERACT_PATH = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def setup_tesseract():
    """Configure Tesseract"""
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Configuration OCR optimale trouvée
BEST_OCR_CONFIG = "{best_config}"

# Patterns d'extraction universels
UNIVERSAL_PATTERNS = {{
    'nom_kevin': r'(Kevin)',
    'nom_tillie': r'(Tillie)', 
    'numero': r'(\\d{{1,2}})(?:\\s|$)',
    'taille': r'(\\d{{3}})',  # 3 chiffres
    'poids': r'(\\d{{2,3}})(?:\\s*kg|\\s*kilo)',
    'age': r'(\\d{{2}})(?:\\s*ans?|\\s*years?)',
    'poste': r'(attaquant|attacker|spiker|passeur|setter|central|middle|libero)',
    'selections': r'(\\d+)(?:\\s*sélections?|selections?|caps?)'
}}

# Configuration automatique
setup_tesseract()
'''
    
    try:
        with open('ocr_config_working.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ Configuration fonctionnelle sauvée")
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde: {e}")

def main():
    """Test principal"""
    print("🏐 CORRECTION TESSERACT - PACKS LANGUE")
    print("Résolution du problème de langue française")
    print()
    
    success = fix_tesseract_language()
    
    if success:
        print(f"\n🎉 OCR FONCTIONNEL!")
        print(f"✅ Extraction possible sur les images CV")
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        print(f"1. python enhanced_ocr_extractor.py  # Extraction complète")
        print(f"2. Utilisation config anglais si français indisponible")
    else:
        print(f"\n❌ PROBLÈME PERSISTANT")
        print(f"🔧 Vérifiez l'installation de Tesseract")

if __name__ == "__main__":
    main()