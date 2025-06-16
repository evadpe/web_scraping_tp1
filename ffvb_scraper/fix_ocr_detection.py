# fix_ocr_detection.py
"""
Script pour corriger la détection OCR dans complete_data_extraction.py
"""

def fix_ocr_detection():
    """Corrige la fonction de détection OCR"""
    
    # Nouveau code de détection OCR qui fonctionne
    ocr_detection_code = '''
def check_ocr_availability():
    """Vérifie la disponibilité d'OCR (VERSION CORRIGÉE)"""
    try:
        import pytesseract
        from PIL import Image
        import cv2
        
        # Configuration Tesseract
        pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
        
        # Test rapide
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract détecté: {version}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur OCR: {e}")
        return False
'''
    
    print("🔧 CORRECTION DÉTECTION OCR")
    print("=" * 30)
    
    # Lire le fichier actuel
    try:
        with open('complete_data_extraction.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer la fonction de détection OCR
        import re
        
        # Pattern pour trouver la fonction actuelle
        pattern = r'def check_ocr_availability\(\):.*?return False'
        
        # Remplacement
        new_content = re.sub(pattern, ocr_detection_code.strip(), content, flags=re.DOTALL)
        
        # Sauvegarder
        with open('complete_data_extraction.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Détection OCR corrigée")
        print("🔄 Relancez: python complete_data_extraction.py")
        
    except Exception as e:
        print(f"❌ Erreur correction: {e}")
        print("💡 Solution alternative: utilisez directement l'extracteur optimisé")

def test_ocr_direct():
    """Test direct de l'OCR"""
    print("\n🧪 TEST DIRECT OCR:")
    print("-" * 20)
    
    try:
        import pytesseract
        from PIL import Image
        
        # Configuration
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        # Test
        version = pytesseract.get_tesseract_version()
        print(f"✅ OCR fonctionne: Tesseract {version}")
        return True
        
    except Exception as e:
        print(f"❌ OCR ne fonctionne pas: {e}")
        return False

if __name__ == "__main__":
    print("🔧 CORRECTION DÉTECTION OCR - COMPLETE_DATA_EXTRACTION")
    print()
    
    # Test direct d'abord
    ocr_works = test_ocr_direct()
    
    if ocr_works:
        print("\n📋 L'OCR fonctionne mais n'est pas détecté correctement")
        print("🔧 Correction du fichier complete_data_extraction.py...")
        fix_ocr_detection()
    else:
        print("\n❌ L'OCR ne fonctionne vraiment pas")
        print("📦 Vérifiez l'installation de Tesseract")