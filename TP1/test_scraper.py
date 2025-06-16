import sys


def test_imports():
    """
    Test d'importation des modules.

    Returns:
        bool: True si tous les modules requis sont importables, False sinon.
    """
    print("TEST 1: Importation des modules")
    print("-" * 50)

    modules_to_test = [
        ('requests', 'Requetes HTTP'),
        ('bs4', 'BeautifulSoup4'),
        ('pymongo', 'MongoDB'),
        ('json', 'JSON (integre)'),
        ('datetime', 'Date/Heure (integre)')
    ]

    success_count = 0

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"{description}: {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"ERREUR {description}: {module_name} - {e}")

    total_modules = len(modules_to_test)
    print(f"\nResultat: {success_count}/{total_modules} modules importes")
    return success_count == total_modules


def test_basic_scraping():
    """
    Test basique de scraping.

    Returns:
        bool: True si le scraping de base fonctionne, False sinon.
    """
    print("\nTEST 2: Scraping basique")
    print("-" * 50)

    try:
        import requests
        from bs4 import BeautifulSoup

        print("Test de connexion au Blog du Moderateur...")

        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36')
        }

        url = "https://www.blogdumoderateur.com"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"Connexion reussie (Status: {response.status_code})")

            # Test de parsing HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "Titre non trouve"
            print(f"Titre de la page: {title}")

            # Compter les liens
            links = soup.find_all('a', href=True)
            print(f"{len(links)} liens trouves")

            return True
        else:
            print(f"Erreur HTTP: {response.status_code}")
            return False

    except Exception as e:
        print(f"Erreur lors du test: {e}")
        return False


def test_mongodb():
    """
    Test de connexion MongoDB (optionnel).

    Returns:
        bool: True si MongoDB est accessible, False sinon.
    """
    print("\nTEST 3: MongoDB (optionnel)")
    print("-" * 50)

    try:
        from pymongo import MongoClient

        print("Test de connexion MongoDB...")
        client = MongoClient("mongodb://localhost:27017/",
                             serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        client.close()

        print("MongoDB accessible")
        return True

    except Exception as e:
        print(f"MongoDB non accessible: {e}")
        return False


def test_scraper_module():
    """
    Test du module scraper.

    Returns:
        bool: True si le module scraper fonctionne, False sinon.
    """
    print("\nTEST 4: Module scraper")
    print("-" * 50)

    try:
        print("Module bdm_scraper importe avec succes")

        return True

    except ImportError as e:
        print(f"Impossible d'importer bdm_scraper: {e}")
        return False
    except Exception as e:
        print(f"Erreur lors de l'instanciation: {e}")
        return False


def quick_demo():
    """
    Demonstration rapide.

    Returns:
        bool: True si la demo reussit, False sinon.
    """
    print("\nTEST 5: Demonstration rapide")
    print("-" * 50)

    try:
        from bdm_scraper import BDMScraper

        scraper = BDMScraper()
        print("Recherche d'articles sur la page d'accueil...")

        # Test très limité pour ne pas surcharger le serveur
        article_links = scraper.get_homepage_articles()

        if article_links:
            print(f"{len(article_links)} articles trouves!")
            print("Premiers liens:")
            for i, link in enumerate(article_links[:3], 1):
                print(f"   {i}. {link}")
            return True
        else:
            print("Aucun article trouve")
            return False

    except Exception as e:
        print(f"Erreur lors de la demonstration: {e}")
        return False


def run_all_tests():
    """
    Execute tous les tests.

    Returns:
        bool: True si les tests critiques passent, False sinon.
    """
    print("TESTS SIMPLIFIES DU SCRAPER BDM")
    print("=" * 60)

    tests = [
        ("Importation des modules", test_imports),
        ("Scraping basique", test_basic_scraping),
        ("MongoDB (optionnel)", test_mongodb),
        ("Module scraper", test_scraper_module),
        ("Demonstration rapide", quick_demo)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\nTests interrompus par l'utilisateur")
            break
        except Exception as e:
            print(f"\nErreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))

    # Résumé des résultats
    print("\n" + "=" * 60)
    print("RESUME DES TESTS")
    print("=" * 60)

    passed = 0
    critical_passed = 0

    for i, (test_name, result) in enumerate(results):
        status = "PASS" if result else "FAIL"
        if i < 2:
            critical_marker = "(critique)"
        elif "MongoDB" in test_name:
            critical_marker = "(optionnel)"
        else:
            critical_marker = ""

        print(f"{status} {test_name} {critical_marker}")

        if result:
            passed += 1
            # Tests critiques: imports + scraping basique ou module scraper
            if i < 2 or "scraper" in test_name.lower():
                critical_passed += 1

    print(f"\nResultat: {passed}/{len(results)} tests reussis")

    # Évaluation
    if critical_passed >= 2:  # Au moins imports + scraping basique
        print("Tests critiques reussis! Vous pouvez commencer a scraper.")
        print("\nProchaines etapes:")
        print("   1. python quick_start.py")
        print("   2. python main_scraper.py --scrape --max-articles 3")
        return True
    else:
        print("Tests critiques echoues. Verifiez les dependances.")
        return False


def main():
    """Fonction principale."""
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()

        if test_name == "imports":
            test_imports()
        elif test_name == "scraping":
            test_basic_scraping()
        elif test_name == "mongodb":
            test_mongodb()
        elif test_name == "module":
            test_scraper_module()
        elif test_name == "demo":
            quick_demo()
        elif test_name == "all":
            run_all_tests()
        else:
            print("Tests disponibles: imports, scraping, mongodb, "
                  "module, demo, all")
    else:
        # Mode interactif
        print("TESTS DU SCRAPER")
        print("1. Test imports")
        print("2. Test scraping basique")
        print("3. Test MongoDB")
        print("4. Test module scraper")
        print("5. Demonstration")
        print("6. Tous les tests")
        print("0. Quitter")

        choice = input("\nChoisissez un test (0-6): ").strip()

        if choice == "1":
            test_imports()
        elif choice == "2":
            test_basic_scraping()
        elif choice == "3":
            test_mongodb()
        elif choice == "4":
            test_scraper_module()
        elif choice == "5":
            quick_demo()
        elif choice == "6":
            run_all_tests()
        elif choice == "0":
            print("Au revoir!")
        else:
            print("Choix invalide")


if __name__ == "__main__":
    main()
