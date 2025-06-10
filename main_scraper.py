import argparse
import json
import sys
from datetime import datetime

from bdm_scraper import BDMScraper
from mongodb_handler import MongoDBHandler


def make_json_serializable(obj):
    """
    Convertit un objet en format serializable JSON.

    Args:
        obj: L'objet à convertir.

    Returns:
        L'objet converti en format serializable JSON.
    """
    from bson import ObjectId

    if isinstance(obj, dict):
        return {key: make_json_serializable(value)
                for key, value in obj.items() if key != '_id'}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def scrape_and_save(max_articles=None, save_json=True):
    """
    Scrape les articles et les sauvegarde en MongoDB.

    Args:
        max_articles (int, optional): Nombre maximum d'articles à scraper.
        save_json (bool): Sauvegarder aussi en JSON.

    Returns:
        bool: True si succès, False sinon.
    """
    print("DEBUT DU SCRAPING DU BLOG DU MODERATEUR")
    print("=" * 60)

    # Initialiser le scraper
    scraper = BDMScraper()

    # Initialiser MongoDB
    try:
        db_handler = MongoDBHandler()
    except Exception as e:
        print(f"Impossible de se connecter a MongoDB: {e}")
        print("Assurez-vous que MongoDB est demarre")
        return False

    try:
        # Scraper les articles
        limit_text = max_articles or 'aucune'
        print(f"Scraping des articles (limite: {limit_text})...")
        articles = scraper.scrape_homepage_articles(max_articles=max_articles)

        if not articles:
            print("Aucun article recupere")
            return False

        # Sauvegarder en MongoDB
        print(f"\nSauvegarde de {len(articles)} articles en MongoDB...")
        save_stats = db_handler.save_articles(articles)

        # Sauvegarder en JSON si demandé
        if save_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"bdm_articles_{timestamp}.json"

            # Nettoyer les données pour JSON
            clean_articles = make_json_serializable(articles)

            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(clean_articles, f, ensure_ascii=False, indent=2)

            print(f"Sauvegarde JSON: {json_filename}")

        # Afficher le résumé
        print("\nRESUME FINAL")
        print(f"   Articles scrapes: {len(articles)}")
        print(f"   Sauvegardes en MongoDB: {save_stats['saved']}")
        print(f"   Doublons ignores: {save_stats['duplicates']}")
        print(f"   Erreurs: {save_stats['errors']}")

        # Afficher quelques exemples
        print("\nARTICLES RECUPERES:")
        for i, article in enumerate(articles[:5], 1):
            title_preview = article['title'][:60]
            print(f"   {i}. {title_preview}...")
            author = article['author'] or 'Non trouve'
            print(f"      Auteur: {author}")
            publish_date = article['publish_date'] or 'Non trouvee'
            print(f"      Date: {publish_date}")
            print(f"      Images: {len(article['images'])}")

        if len(articles) > 5:
            remaining = len(articles) - 5
            print(f"   ... et {remaining} autres articles")

        return True

    except KeyboardInterrupt:
        print("\nScraping interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"\nErreur lors du scraping: {e}")
        return False
    finally:
        # Fermer la connexion
        db_handler.close_connection()


def search_articles():
    """Interface de recherche d'articles."""
    print("RECHERCHE D'ARTICLES")
    print("=" * 40)

    try:
        db_handler = MongoDBHandler()
    except Exception as e:
        print(f"Impossible de se connecter a MongoDB: {e}")
        return

    try:
        while True:
            print("\nOptions de recherche:")
            print("1. Recherche par categorie/sous-categorie")
            print("2. Recherche avancee")
            print("3. Voir toutes les categories")
            print("4. Voir tous les auteurs")
            print("5. Statistiques")
            print("0. Quitter")

            choice = input("\nChoisissez une option (0-5): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                search_by_category(db_handler)
            elif choice == "2":
                advanced_search(db_handler)
            elif choice == "3":
                show_categories(db_handler)
            elif choice == "4":
                show_authors(db_handler)
            elif choice == "5":
                show_statistics(db_handler)
            else:
                print("Option invalide")

    finally:
        db_handler.close_connection()


def search_by_category(db_handler):
    """
    Recherche par catégorie.

    Args:
        db_handler: Gestionnaire de base de données MongoDB.
    """
    print("\nRecherche par categorie")

    category = input("Entrez la categorie ou sous-categorie: ").strip()

    if not category:
        print("Categorie vide")
        return

    articles = db_handler.get_articles_by_category(category)
    display_search_results(articles)


def advanced_search(db_handler):
    """
    Recherche avancée.

    Args:
        db_handler: Gestionnaire de base de données MongoDB.
    """
    print("\nRecherche avancee")
    print("Laissez vide pour ignorer un critere")

    title = input("Mot-cle dans le titre: ").strip() or None
    author = input("Auteur: ").strip() or None
    category = input("Categorie: ").strip() or None
    date_start = input("Date debut (YYYY-MM-DD): ").strip() or None
    date_end = input("Date fin (YYYY-MM-DD): ").strip() or None

    try:
        limit_input = input("Nombre max de resultats (defaut: 20): ").strip()
        limit = int(limit_input) if limit_input else 20
    except ValueError:
        limit = 20

    articles = db_handler.search_articles(
        title_substring=title,
        author=author,
        category=category,
        date_start=date_start,
        date_end=date_end,
        limit=limit
    )

    display_search_results(articles)


def display_search_results(articles):
    """
    Affiche les résultats de recherche.

    Args:
        articles (list): Liste des articles trouvés.
    """
    if not articles:
        print("Aucun article trouve")
        return

    print(f"\n{len(articles)} article(s) trouve(s):")
    print("-" * 80)

    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        publish_date = article.get('publish_date', 'Non renseignee')
        print(f"   Date: {publish_date}")
        author = article.get('author', 'Non renseigne')
        print(f"   Auteur: {author}")
        subcategory = article.get('subcategory', 'Non renseignee')
        print(f"   Categorie: {subcategory}")
        print(f"   URL: {article['url']}")

        if article.get('summary'):
            summary = article['summary']
            if len(summary) > 100:
                summary = summary[:100] + "..."
            print(f"   Resume: {summary}")

        print()


def show_categories(db_handler):
    """
    Affiche toutes les catégories.

    Args:
        db_handler: Gestionnaire de base de données MongoDB.
    """
    categories = db_handler.get_all_categories()

    print(f"\n{len(categories)} categories trouvees:")
    for i, category in enumerate(categories, 1):
        print(f"   {i}. {category}")


def show_authors(db_handler):
    """
    Affiche tous les auteurs.

    Args:
        db_handler: Gestionnaire de base de données MongoDB.
    """
    authors = db_handler.get_all_authors()

    print(f"\n{len(authors)} auteurs trouves:")
    for i, author in enumerate(authors, 1):
        print(f"   {i}. {author}")


def show_statistics(db_handler):
    """
    Affiche les statistiques.

    Args:
        db_handler: Gestionnaire de base de données MongoDB.
    """
    stats = db_handler.get_statistics()

    print("\nSTATISTIQUES DE LA BASE DE DONNEES")
    print("-" * 40)
    print(f"Total articles: {stats.get('total_articles', 0)}")
    print(f"Total categories: {stats.get('total_categories', 0)}")
    print(f"Total auteurs: {stats.get('total_authors', 0)}")

    date_range = stats.get('date_range', {})
    if date_range.get('oldest'):
        oldest = date_range['oldest']
        newest = date_range['newest']
        print(f"Periode couverte: {oldest} a {newest}")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Scraper du Blog du Moderateur"
    )
    parser.add_argument("--scrape", action="store_true",
                        help="Scraper les articles")
    parser.add_argument("--search", action="store_true",
                        help="Interface de recherche")
    parser.add_argument("--max-articles", type=int,
                        help="Nombre max d'articles a scraper")
    parser.add_argument("--no-json", action="store_true",
                        help="Ne pas sauvegarder en JSON")

    args = parser.parse_args()

    if args.scrape:
        success = scrape_and_save(
            max_articles=args.max_articles,
            save_json=not args.no_json
        )
        sys.exit(0 if success else 1)

    elif args.search:
        search_articles()

    else:
        # Mode interactif
        print("SCRAPER DU BLOG DU MODERATEUR")
        print("=" * 50)
        print("1. Scraper les articles")
        print("2. Rechercher dans la base")
        print("0. Quitter")

        choice = input("\nChoisissez une option (0-2): ").strip()

        if choice == "1":
            try:
                max_input = input("Nombre max d'articles (Entree pour tous): ")
                max_articles = int(
                    max_input.strip()) if max_input.strip() else None
            except ValueError:
                max_articles = None

            scrape_and_save(max_articles=max_articles)

        elif choice == "2":
            search_articles()


if __name__ == "__main__":
    main()
