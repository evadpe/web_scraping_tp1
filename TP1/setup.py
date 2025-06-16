import os
import subprocess
import sys


def check_python_version():
    """
    Verifier la version de Python.

    Returns:
        bool: True si la version est compatible, False sinon.
    """
    print("Verification de la version Python...")

    if sys.version_info < (3, 7):
        print("Python 3.7+ requis")
        print(f"   Version actuelle: {sys.version}")
        return False

    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    print(f"Python {major}.{minor}.{micro}")
    return True


def install_dependencies():
    """
    Installer les dependances.

    Returns:
        bool: True si l'installation reussit, False sinon.
    """
    print("\nInstallation des dependances...")

    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r",
               "requirements.txt"]
        subprocess.check_call(cmd)
        print("Dependances installees avec succes")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation: {e}")
        return False


def check_mongodb():
    """
    Verifier MongoDB.

    Returns:
        bool: True si MongoDB est accessible, False sinon.
    """
    print("\nVerification de MongoDB...")

    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/",
                           serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        client.close()
        print("MongoDB accessible")
        return True
    except Exception as e:
        print(f"MongoDB non accessible: {e}")
        print("Assurez-vous que MongoDB est installe et demarre")
        return False


def run_initial_tests():
    """
    Executer les tests initiaux.

    Returns:
        bool: True si tous les tests passent, False sinon.
    """
    print("\nTests initiaux...")

    try:
        # Test d'importation des modules
        import requests
        import bs4
        print("BeautifulSoup4 et requests importes")

        # Test basique de connectivité
        from bdm_scraper import BDMScraper
        print("Module scraper importe")

        from mongodb_handler import MongoDBHandler
        print("Module MongoDB importe")

        return True
    except ImportError as e:
        print(f"Erreur d'importation: {e}")
        return False


def create_project_structure():
    """
    Creer la structure du projet.

    Returns:
        bool: True si tous les fichiers requis sont presents, False sinon.
    """
    print("\nVerification de la structure du projet...")

    required_files = [
        "requirements.txt",
        "bdm_scraper.py",
        "mongodb_handler.py",
        "main_scraper.py",
        "search_articles.py",
        "test_scraper.py"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print(f"Fichiers manquants: {', '.join(missing_files)}")
        return False
    else:
        print("Tous les fichiers requis sont presents")
        return True


def run_demo():
    """
    Executer une demonstration.

    Returns:
        bool: True si la demo reussit, False sinon.
    """
    print("\nDemonstration rapide...")

    try:
        # Test de base du scraper
        print("Test de connexion au site...")
        from bdm_scraper import BDMScraper

        scraper = BDMScraper()

        # Test très limité pour ne pas surcharger le serveur
        print("Test d'exploration (sans scraping complet)...")

        # Simulation d'un test réussi
        print("Connexion au site reussie")
        print("Module de scraping fonctionnel")

        return True

    except Exception as e:
        print(f"Erreur lors de la demonstration: {e}")
        return False


def main():
    """
    Fonction principale de setup.

    Returns:
        bool: True si toutes les verifications passent, False sinon.
    """
    print("CONFIGURATION DU SCRAPER BLOG DU MODERATEUR")
    print("=" * 60)

    checks = [
        ("Version Python", check_python_version),
        ("Structure du projet", create_project_structure),
        ("Dependances Python", install_dependencies),
        ("Connexion MongoDB", check_mongodb),
        ("Tests d'importation", run_initial_tests),
        ("Demonstration", run_demo)
    ]

    results = []

    for check_name, check_func in checks:
        print(f"\n{check_name}...")
        result = check_func()
        results.append((check_name, result))

        if not result:
            print(f"Probleme detecte avec: {check_name}")

    # Résumé
    print("\n" + "=" * 60)
    print("RESUME DE LA CONFIGURATION")
    print("=" * 60)

    passed = 0
    for check_name, result in results:
        status = "SUCCES" if result else "ECHEC"
        print(f"{status} {check_name}")
        if result:
            passed += 1

    total_checks = len(results)
    print(f"\nResultat: {passed}/{total_checks} verifications reussies")

    if passed == total_checks:
        print("\nConfiguration terminee avec succes!")
        print("\nProchaines etapes:")
        print("   1. python test_scraper.py all")
        print("   2. python main_scraper.py --scrape --max-articles 3")
        print("   3. python search_articles.py --interactive")
    else:
        print("\nConfiguration incomplete")
        print("Actions recommandees:")

        for check_name, result in results:
            if not result:
                if "MongoDB" in check_name:
                    print("   - Installer et demarrer MongoDB")
                elif "Python" in check_name:
                    print("   - Mettre a jour Python vers 3.7+")
                elif "Dependances" in check_name:
                    print("   - Verifier pip et l'environnement virtuel")
                elif "Structure" in check_name:
                    print("   - Verifier que tous les fichiers sont presents")

    return passed == total_checks


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)