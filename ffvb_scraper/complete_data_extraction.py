# complete_data_extraction.py
"""
Script complet pour extraire TOUTES les données des joueurs FFVB
Combine vos données existantes + OCR + validation + rapport final
"""

import csv
import json
import os
import sys
from datetime import datetime
import subprocess

def main():
    """Menu principal pour extraction complète"""
    print("🏐 EXTRACTION COMPLÈTE DONNÉES FFVB")
    print("=" * 40)
    print("🎯 Objectif: Récupérer toutes les données manquantes")
    print("📊 Vous avez déjà: 51 joueurs avec noms/numéros/images")
    print("🎯 À extraire: poste, taille, poids, âge, club, stats...")
    print()
    
    # Vérifier les fichiers existants
    status = check_existing_files()
    print_status(status)
    
    print("\n📋 OPTIONS D'EXTRACTION:")
    print("1. 🖼️  Extraction OCR complète (RECOMMANDÉ)")
    print("2. 🧪 Test OCR sur quelques joueurs d'abord")
    print("3. 📊 Analyser les données actuelles uniquement")
    print("4. 🔧 Configuration et dépendances")
    print("5. 📋 Rapport final des données existantes")
    
    try:
        choice = input("\nVotre choix (1-5): ").strip()
        
        if choice == "1":
            run_complete_ocr_extraction()
        elif choice == "2":
            run_test_ocr()
        elif choice == "3":
            analyze_current_data()
        elif choice == "4":
            setup_dependencies()
        elif choice == "5":
            generate_final_report()
        else:
            print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

def check_existing_files():
    """Vérifie les fichiers existants et leur statut"""
    status = {
        'base_csv': os.path.exists('ffvb_players_complete.csv'),
        'enhanced_csv': os.path.exists('ffvb_players_enhanced_complete.csv'),
        'ocr_available': check_ocr_availability(),
        'player_count': 0,
        'completeness': 0
    }
    
    # Analyser le fichier de base
    if status['base_csv']:
        try:
            with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                players = list(reader)
                status['player_count'] = len(players)
                
                # Calculer complétude moyenne
                if players:
                    important_fields = ['poste', 'taille', 'poids', 'age', 'club_actuel']
                    total_completeness = 0
                    
                    for player in players:
                        filled = sum(1 for field in important_fields if player.get(field, '').strip())
                        total_completeness += (filled / len(important_fields)) * 100
                    
                    status['completeness'] = total_completeness / len(players)
        
        except Exception as e:
            print(f"⚠️ Erreur lecture CSV: {e}")
    
    return status

def print_status(status):
    """Affiche le statut des fichiers"""
    print("\n📊 STATUT ACTUEL:")
    print("-" * 20)
    
    if status['base_csv']:
        print(f"✅ Données de base: {status['player_count']} joueurs")
        print(f"📈 Complétude: {status['completeness']:.1f}%")
    else:
        print("❌ Aucune donnée de base trouvée")
        print("💡 Lancez d'abord le scraper avancé")
    
    if status['enhanced_csv']:
        print("✅ Données enrichies disponibles")
    else:
        print("⚠️ Données enrichies manquantes")
    
    if status['ocr_available']:
        print("✅ OCR disponible")
    else:
        print("❌ OCR non disponible")

def check_ocr_availability():
    """Vérifie la disponibilité d'OCR"""
    try:
        import pytesseract
        import PIL
        import cv2
        pytesseract.get_tesseract_version()
        return True
    except:
        return False

def run_complete_ocr_extraction():
    """Lance l'extraction OCR complète"""
    print("\n🖼️ LANCEMENT EXTRACTION OCR COMPLÈTE")
    print("=" * 45)
    
    if not check_ocr_availability():
        print("❌ OCR non disponible")
        print("📦 Installation requise:")
        print("   pip install pytesseract pillow opencv-python")
        print("   + Tesseract système")
        return
    
    if not os.path.exists('ffvb_players_complete.csv'):
        print("❌ Fichier de base manquant: ffvb_players_complete.csv")
        print("💡 Lancez d'abord le scraper avancé")
        return
    
    try:
        # Importer et lancer l'extracteur OCR
        print("🚀 Lancement de l'extraction OCR...")
        
        # Utiliser le script OCR amélioré
        result = subprocess.run([
            sys.executable, '-c',
            """
from enhanced_ocr_extractor import EnhancedOCRExtractor
extractor = EnhancedOCRExtractor()
extractor.process_all_players()
"""
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Extraction OCR terminée!")
            analyze_ocr_results()
        else:
            print(f"❌ Erreur extraction: {result.stderr}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")

def run_test_ocr():
    """Lance un test OCR sur quelques joueurs"""
    print("\n🧪 TEST OCR SUR ÉCHANTILLON")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, 'quick_ocr_test.py'
        ], capture_output=False)
        
        if result.returncode == 0:
            print("✅ Test OCR terminé")
        else:
            print("⚠️ Test OCR avec erreurs")
    
    except Exception as e:
        print(f"❌ Erreur test: {e}")

def analyze_current_data():
    """Analyse les données actuelles en détail"""
    print("\n📊 ANALYSE DES DONNÉES ACTUELLES")
    print("=" * 35)
    
    if not os.path.exists('ffvb_players_complete.csv'):
        print("❌ Fichier ffvb_players_complete.csv non trouvé")
        return
    
    try:
        with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        print(f"📊 Total joueurs: {len(players)}")
        
        # Analyser les champs remplis
        all_fields = list(players[0].keys()) if players else []
        field_stats = {}
        
        for field in all_fields:
            filled_count = sum(1 for player in players if player.get(field, '').strip())
            field_stats[field] = {
                'filled': filled_count,
                'percentage': (filled_count / len(players)) * 100 if players else 0
            }
        
        # Afficher les statistiques
        print(f"\n📈 COMPLÉTUDE PAR CHAMP:")
        for field, stats in sorted(field_stats.items(), key=lambda x: x[1]['percentage'], reverse=True):
            if stats['percentage'] > 0:
                print(f"   {field}: {stats['filled']}/{len(players)} ({stats['percentage']:.1f}%)")
        
        # Identifier les données manquantes critiques
        critical_missing = []
        important_fields = ['poste', 'taille', 'poids', 'age', 'club_actuel', 'selections']
        
        for field in important_fields:
            if field_stats.get(field, {}).get('percentage', 0) < 10:
                critical_missing.append(field)
        
        if critical_missing:
            print(f"\n⚠️ DONNÉES CRITIQUES MANQUANTES:")
            for field in critical_missing:
                print(f"   - {field}")
            
            print(f"\n💡 RECOMMANDATION:")
            print(f"   Ces données sont probablement dans les images CV")
            print(f"   → Utilisez l'extraction OCR (option 1)")
        
        # Analyser les URLs d'images
        images_count = sum(1 for player in players if player.get('url_cv_image', '').strip())
        print(f"\n🖼️ Images CV disponibles: {images_count}/{len(players)}")
        
        if images_count > 0:
            print(f"✅ OCR possible sur {images_count} joueurs")
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")

def analyze_ocr_results():
    """Analyse les résultats de l'extraction OCR"""
    enhanced_file = 'ffvb_players_enhanced_complete.csv'
    
    if not os.path.exists(enhanced_file):
        print(f"⚠️ Fichier {enhanced_file} non trouvé")
        return
    
    try:
        with open(enhanced_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            enhanced_players = list(reader)
        
        print(f"\n📊 RÉSULTATS OCR:")
        print(f"   Joueurs traités: {len(enhanced_players)}")
        
        # Analyser la complétude après OCR
        important_fields = ['poste', 'taille', 'poids', 'age', 'club']
        
        for field in important_fields:
            filled_count = sum(1 for player in enhanced_players if player.get(field, '').strip())
            percentage = (filled_count / len(enhanced_players)) * 100 if enhanced_players else 0
            print(f"   {field}: {filled_count}/{len(enhanced_players)} ({percentage:.1f}%)")
        
        # Score de complétude moyen
        scores = [float(player.get('completeness_score', 0)) for player in enhanced_players]
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"   Score moyen: {avg_score:.1f}%")
        
        # Exemples de joueurs bien extraits
        well_extracted = [p for p in enhanced_players if float(p.get('completeness_score', 0)) > 60]
        if well_extracted:
            print(f"\n✅ Joueurs bien extraits ({len(well_extracted)}):")
            for player in well_extracted[:3]:
                name = player.get('nom_joueur', 'N/A')
                poste = player.get('poste', 'N/A')
                taille = player.get('taille', 'N/A')
                score = player.get('completeness_score', 0)
                print(f"   - {name} ({poste}, {taille}cm) - {score}%")
    
    except Exception as e:
        print(f"❌ Erreur analyse OCR: {e}")

def setup_dependencies():
    """Configure les dépendances nécessaires"""
    print("\n🔧 CONFIGURATION DES DÉPENDANCES")
    print("=" * 35)
    
    # Vérifier Python
    print(f"🐍 Python: {sys.version}")
    
    # Vérifier les packages
    packages = [
        ('scrapy', 'Scraping web'),
        ('requests', 'Requêtes HTTP'),
        ('beautifulsoup4', 'Parsing HTML'),
        ('pytesseract', 'OCR Tesseract'),
        ('pillow', 'Traitement images'),
        ('opencv-python', 'Vision par ordinateur')
    ]
    
    print(f"\n📦 VÉRIFICATION DES PACKAGES:")
    missing_packages = []
    
    for package, description in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}: OK")
        except ImportError:
            print(f"   ❌ {package}: MANQUANT ({description})")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📥 INSTALLATION REQUISE:")
        install_cmd = f"pip install {' '.join(missing_packages)}"
        print(f"   {install_cmd}")
        
        install_now = input("\nInstaller maintenant? (o/n): ").strip().lower()
        if install_now == 'o':
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages)
                print("✅ Installation terminée")
            except Exception as e:
                print(f"❌ Erreur installation: {e}")
    
    # Vérifier Tesseract système
    print(f"\n🔍 TESSERACT SYSTÈME:")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"   ✅ Tesseract {version}")
    except:
        print(f"   ❌ Tesseract non installé")
        print(f"   📥 Installation requise:")
        print(f"      Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print(f"      Linux: sudo apt install tesseract-ocr")
        print(f"      macOS: brew install tesseract")

def generate_final_report():
    """Génère un rapport final complet"""
    print("\n📋 GÉNÉRATION RAPPORT FINAL")
    print("=" * 30)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"ffvb_rapport_final_{timestamp}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🏐 RAPPORT FINAL - EXTRACTION DONNÉES FFVB\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            # Analyser fichier de base
            if os.path.exists('ffvb_players_complete.csv'):
                with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as base_f:
                    base_reader = csv.DictReader(base_f)
                    base_players = list(base_reader)
                
                f.write(f"📊 DONNÉES DE BASE:\n")
                f.write(f"   Joueurs extraits: {len(base_players)}\n")
                f.write(f"   Source: Scraper web FFVB\n\n")
                
                # Top 10 joueurs
                f.write(f"👥 JOUEURS IDENTIFIÉS (échantillon):\n")
                for i, player in enumerate(base_players[:10], 1):
                    nom = player.get('nom_joueur', 'N/A')
                    numero = player.get('numero', 'N/A')
                    f.write(f"   {i:2d}. #{numero} - {nom}\n")
                
                if len(base_players) > 10:
                    f.write(f"   ... et {len(base_players) - 10} autres\n")
            
            # Analyser fichier enrichi si disponible
            if os.path.exists('ffvb_players_enhanced_complete.csv'):
                with open('ffvb_players_enhanced_complete.csv', 'r', encoding='utf-8') as enh_f:
                    enh_reader = csv.DictReader(enh_f)
                    enh_players = list(enh_reader)
                
                f.write(f"\n🖼️ DONNÉES ENRICHIES (OCR):\n")
                f.write(f"   Joueurs traités: {len(enh_players)}\n")
                
                # Statistiques de complétude
                important_fields = ['poste', 'taille', 'poids', 'age', 'club']
                f.write(f"\n📈 COMPLÉTUDE DES DONNÉES:\n")
                
                for field in important_fields:
                    filled = sum(1 for p in enh_players if p.get(field, '').strip())
                    pct = (filled / len(enh_players)) * 100 if enh_players else 0
                    f.write(f"   {field}: {filled}/{len(enh_players)} ({pct:.1f}%)\n")
            
            f.write(f"\n✅ EXTRACTION TERMINÉE\n")
            f.write(f"📄 Rapport généré: {report_file}\n")
        
        print(f"✅ Rapport sauvegardé: {report_file}")
        
        # Afficher un résumé
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\n📄 APERÇU DU RAPPORT:")
            print("-" * 30)
            print(content[:800] + "..." if len(content) > 800 else content)
    
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")

if __name__ == "__main__":
    main()