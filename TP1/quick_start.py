def quick_test():
    """
    Test rapide du scraper.

    Returns:
        bool: True si le test reussit, False sinon.
    """
    print("DEMARRAGE RAPIDE - SCRAPER BDM")
    print("=" * 50)

    try:
        # Import et test du scraper
        print("Test de connexion au site...")
        from bdm_scraper import BDMScraper

        scraper = BDMScraper()

        # Test d'exploration de la page d'accueil
        print("Exploration de la page d'accueil...")
        article_links = scraper.get_homepage_articles()

        if not article_links:
            print("Aucun article trouve")
            return False

        print(f"{len(article_links)} articles trouves!")

        # Afficher quelques exemples
        print("\nPremiers articles trouves:")
        for i, link in enumerate(article_links[:3], 1):
            print(f"   {i}. {link}")

        # Test de scraping d'un article
        print("\nTest de scraping du premier article...")
        test_article = scraper.scrape_article(article_links[0])

        if test_article:
            print("Scraping reussi!")
            print(f"   Titre: {test_article['title']}")
            author = test_article['author'] or 'Non trouve'
            print(f"   Auteur: {author}")
            publish_date = test_article['publish_date'] or 'Non trouvee'
            print(f"   Date: {publish_date}")
            subcategory = test_article['subcategory'] or 'Non trouvee'
            print(f"   Categorie: {subcategory}")
            print(f"   Images: {len(test_article['images'])} trouvees")
            content_length = len(test_article['content'] or '')
            print(f"   Contenu: {content_length} caracteres")
        else:
            print("Echec du scraping")
            return False

        return True

    except Exception as e:
        print(f"Erreur: {e}")
        return False


def quick_mongodb_test():
    """
    Test rapide de MongoDB.

    Returns:
        bool: True si le test reussit, False sinon.
    """
    print("\nTEST MONGODB")
    print("-" * 30)

    try:
        from mongodb_handler import MongoDBHandler

        print("Connexion a MongoDB...")
        db_handler = MongoDBHandler()

        # Test des statistiques
        stats = db_handler.get_statistics()
        print("Connexion reussie!")
        print(f"   Articles en base: {stats.get('total_articles', 0)}")
        print(f"   Categories: {stats.get('total_categories', 0)}")

        db_handler.close_connection()
        return True

    except Exception as e:
        print(f"Erreur MongoDB: {e}")
        print("Assurez-vous que MongoDB est demarre")
        return False


def run_quick_scraping():
    """
    Scraping rapide de quelques articles.

    Returns:
        bool: True si le scraping reussit, False sinon.
    """
    print("\nSCRAPING RAPIDE")
    print("-" * 30)

    try:
        from bdm_scraper import BDMScraper
        from mongodb_handler import MongoDBHandler

        # Scraper
        scraper = BDMScraper()
        print("Scraping de 2 articles pour test...")

        articles = scraper.scrape_homepage_articles(max_articles=2)

        if not articles:
            print("Aucun article recupere")
            return False

        print(f"{len(articles)} articles scrapes!")

        # Sauvegarde en MongoDB
        try:
            db_handler = MongoDBHandler()
            print("Sauvegarde en MongoDB...")

            stats = db_handler.save_articles(articles)
            saved_count = stats['saved']
            print(f"Sauvegarde terminee: {saved_count} nouveaux articles")

            db_handler.close_connection()
        except Exception as e:
            print(f"Erreur MongoDB (articles scrapes mais non sauves): {e}")

        # Afficher les résultats
        print("\nArticles recuperes:")
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   {article['url']}")
            author = article['author'] or 'Auteur inconnu'
            print(f"   {author}")
            publish_date = article['publish_date'] or 'Date inconnue'
            print(f"   {publish_date}")

        return True

    except Exception as e:
        print(f"Erreur lors du scraping: {e}")
        return False


def main():
    """Menu principal."""
    print("DEMARRAGE RAPIDE - SCRAPER BDM")
    print("=" * 50)
    print("Choisissez une option:")
    print("1. Test de connexion uniquement")
    print("2. Test MongoDB")
    print("3. Scraping rapide (2 articles)")
    print("4. Test complet")
    print("0. Quitter")

    choice = input("\nVotre choix (0-4): ").strip()

    if choice == "1":
        success = quick_test()
    elif choice == "2":
        success = quick_mongodb_test()
    elif choice == "3":
        success = run_quick_scraping()
    elif choice == "4":
        success1 = quick_test()
        success2 = quick_mongodb_test()
        success3 = run_quick_scraping() if success1 and success2 else False
        success = success1 and success2 and success3
    elif choice == "0":
        print("Au revoir!")
        return
    else:
        print("Choix invalide")
        return

    print("\n" + "=" * 50)
    if success:
        print("Test termine avec succes!")
        print("\nProchaines etapes recommandees:")
        print("   • python main_scraper.py --scrape --max-articles 5")
        print("   • python search_articles.py --interactive")
        print("   • python test_scraper.py all")
    else:
        print("Des problemes ont ete detectes")
        print("\nSolutions possibles:")
        print("   • Verifier la connexion internet")
        print("   • Demarrer MongoDB : sudo systemctl start mongodb")
        print("   • Reinstaller les dependances : "
              "pip install -r requirements.txt")


if __name__ == "__main__":
    main()
