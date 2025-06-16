# ocr_config_working.py
"""
Configuration OCR FFVB qui fonctionne - Version Anglais
"""

import pytesseract

# Configuration Tesseract
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def setup_tesseract():
    """Configure Tesseract"""
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Configuration OCR optimale trouvée
BEST_OCR_CONFIG = "--psm 6 -l eng"

# Patterns d'extraction universels
UNIVERSAL_PATTERNS = {
    'nom_kevin': r'(Kevin)',
    'nom_tillie': r'(Tillie)', 
    'numero': r'(\d{1,2})(?:\s|$)',
    'taille': r'(\d{3})',  # 3 chiffres
    'poids': r'(\d{2,3})(?:\s*kg|\s*kilo)',
    'age': r'(\d{2})(?:\s*ans?|\s*years?)',
    'poste': r'(attaquant|attacker|spiker|passeur|setter|central|middle|libero)',
    'selections': r'(\d+)(?:\s*sélections?|selections?|caps?)'
}

# Configuration automatique
setup_tesseract()
