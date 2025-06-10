import argparse
import csv
import json
from datetime import datetime

from mongodb_handler import MongoDBHandler


def get_articles_by_category(category, subcategory=None, limit=None,
                            output_format="console"):
    """
    Recupere tous les articles d'une categorie ou sous-categorie.

    Args:
        category (str): Categorie principale.
        subcategory (str): Sous-categorie (optionnel).
        limit (int): Limite du nombre de resultats (optionnel).
        output_format (str): Format de sortie ('console', 'json', 'csv').

    Returns:
        List[Dict]: Liste des articles trouves.
    """
    try:
        # Connexion a MongoDB
        db_handler = MongoDBHandler()

        # Recherche des articles
        search_term = subcategory if subcategory else category
        print(f"Recherche d'articles pour la categorie: '{search_term}'")

        articles = db_handler.get_articles_by_category(category, subcategory)

        if not articles:
            print(f"Aucun article trouve pour la categorie '{search_term}'")
            return []

        # Appliquer la limite si spécifiée
        if limit and limit > 0:
            articles = articles[:limit]
            print(f"Limitation a {limit} resultats")

        # Affichage selon le format demandé
        if output_format == "console":
            display_articles_console(articles, search_term)
        elif output_format == "json":
            save_articles_json(articles, search_term)
        elif output_format == "csv":
            save_articles_csv(articles, search_term)

        db_handler.close_connection()
        return articles

    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")
        return []


def display_articles_console(articles, category_name):
    """
    Affiche les articles dans la console.

    Args:
        articles (list): Liste des articles a afficher.
        category_name (str): Nom de la categorie.
    """
    print(f"\n{len(articles)} ARTICLES TROUVES POUR '{category_name}'")
    print("=" * 80)

    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")
        publish_date = article.get('publish_date', 'Non renseignee')
        print(f"   Date: {publish_date}")
        author = article.get('author', 'Non renseigne')
        print(f"   Auteur: {author}")
        subcategory = article.get('subcategory', 'Non renseignee')
        print(f"   Categorie: {subcategory}")

        if article.get('summary'):
            summary = article['summary']
            if len(summary) > 100:
                summary = summary[:100] + "..."
            print(f"   Resume: {summary}")

        if article.get('images'):
            print(f"   Images: {len(article['images'])} trouvees")

        content_length = len(article.get('content', ''))
        print(f"   Contenu: {content_length} caracteres")


def save_articles_json(articles, category_name):
    """
    Sauvegarde les articles en JSON.

    Args:
        articles (list): Liste des articles a sauvegarder.
        category_name (str): Nom de la categorie.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_category_name = category_name.replace(' ', '_')
    filename = f"articles_{safe_category_name}_{timestamp}.json"

    try:
        export_data = {
            'category': category_name,
            'total_articles': len(articles),
            'exported_at': datetime.now().isoformat(),
            'articles': articles
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"Articles sauvegardes en JSON: {filename}")

    except Exception as e:
        print(f"Erreur lors de la sauvegarde JSON: {e}")


def save_articles_csv(articles, category_name):
    """
    Sauvegarde les articles en CSV.

    Args:
        articles (list): Liste des articles a sauvegarder.
        category_name (str): Nom de la categorie.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_category_name = category_name.replace(' ', '_')
    filename = f"articles_{safe_category_name}_{timestamp}.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if not articles:
                print("Aucun article a sauvegarder")
                return

            # En-tetes CSV
            fieldnames = [
                'titre', 'url', 'auteur', 'date_publication',
                'categorie', 'resume', 'nb_images', 'taille_contenu'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Ecrire les articles
            for article in articles:
                writer.writerow({
                    'titre': article.get('title', ''),
                    'url': article.get('url', ''),
                    'auteur': article.get('author', ''),
                    'date_publication': article.get('publish_date', ''),
                    'categorie': article.get('subcategory', ''),
                    'resume': article.get('summary', ''),
                    'nb_images': len(article.get('images', {})),
                    'taille_contenu': len(article.get('content', ''))
                })

        print(f"Articles sauvegardes en CSV: {filename}")

    except Exception as e:
        print(f"Erreur lors de la sauvegarde CSV: {e}")


def list_all_categories():
    """Liste toutes les categories disponibles."""
    try:
        db_handler = MongoDBHandler()
        categories = db_handler.get_all_categories()

        if not categories:
            print("Aucune categorie trouvee dans la base de donnees")
            return

        print(f"\n{len(categories)} CATEGORIES DISPONIBLES:")
        print("=" * 50)

        for i, category in enumerate(categories, 1):
            # Compter les articles pour cette catégorie
            articles = db_handler.get_articles_by_category(category)
            print(f"{i:2d}. {category} ({len(articles)} articles)")

        db_handler.close_connection()

    except Exception as e:
        print(f"Erreur lors de la recuperation des categories: {e}")


def interactive_search():
    """Interface interactive pour la recherche."""
    print("RECHERCHE INTERACTIVE D'ARTICLES")
    print("=" * 50)

    try:
        db_handler = MongoDBHandler()

        while True:
            print("\nOptions:")
            print("1. Rechercher par categorie")
            print("2. Voir toutes les categories")
            print("3. Statistiques de la base")
            print("0. Quitter")

            choice = input("\nChoisissez une option (0-3): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                interactive_category_search(db_handler)
            elif choice == "2":
                categories = db_handler.get_all_categories()
                if categories:
                    print("\nCategories disponibles:")
                    for i, cat in enumerate(categories, 1):
                        print(f"   {i}. {cat}")
                else:
                    print("Aucune categorie trouvee")
            elif choice == "3":
                show_database_stats(db_handler)
            else:
                print("Option invalide")

        db_handler.close_connection()

    except Exception as e:
        print(f"Erreur: {e}")


def interactive_category_search(db_handler):
    """
    Recherche interactive par categorie.

    Args:
        db_handler: Gestionnaire de base de donnees MongoDB.
    """
    print("\nRecherche par categorie")

    category = input("Entrez la categorie a rechercher: ").strip()

    if not category:
        print("Categorie vide")
        return

    # Demander si c'est une sous-catégorie spécifique
    is_subcategory_input = input("Est-ce une sous-categorie specifique? "
                                "(o/N): ").strip().lower()
    subcategory = category if is_subcategory_input == 'o' else None
    main_category = category if not subcategory else None

    # Demander la limite
    try:
        limit_input = input("Nombre maximum de resultats "
                           "(Entree pour tous): ").strip()
        limit = int(limit_input) if limit_input else None
    except ValueError:
        limit = None

    # Demander le format de sortie
    print("\nFormat de sortie:")
    print("1. Console (defaut)")
    print("2. JSON")
    print("3. CSV")

    format_choice = input("Choisissez (1-3): ").strip()

    formats = {"1": "console", "2": "json", "3": "csv"}
    output_format = formats.get(format_choice, "console")

    # Effectuer la recherche
    articles = db_handler.get_articles_by_category(main_category, subcategory)

    if not articles:
        print(f"Aucun article trouve pour '{category}'")
        return

    # Appliquer la limite
    if limit and limit > 0:
        articles = articles[:limit]

    # Afficher selon le format
    if output_format == "console":
        display_articles_console(articles, category)
    elif output_format == "json":
        save_articles_json(articles, category)
    elif output_format == "csv":
        save_articles_csv(articles, category)


def show_database_stats(db_handler):
    """
    Affiche les statistiques de la base de donnees.

    Args:
        db_handler: Gestionnaire de base de donnees MongoDB.
    """
    stats = db_handler.get_statistics()

    print("\nSTATISTIQUES DE LA BASE DE DONNEES")
    print("=" * 50)
    print(f"Total articles: {stats.get('total_articles', 0)}")
    print(f"Total categories: {stats.get('total_categories', 0)}")
    print(f"Total auteurs: {stats.get('total_authors', 0)}")

    date_range = stats.get('date_range', {})
    if date_range.get('oldest'):
        oldest = date_range['oldest']
        newest = date_range['newest']
        print(f"Periode: {oldest} a {newest}")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Recherche d'articles par categorie - Blog du Moderateur"
    )
    parser.add_argument("category", nargs="?",
                        help="Categorie a rechercher")
    parser.add_argument("--subcategory",
                        help="Sous-categorie specifique")
    parser.add_argument("--limit", type=int,
                        help="Nombre maximum de resultats")
    parser.add_argument("--format", choices=["console", "json", "csv"],
                        default="console", help="Format de sortie")
    parser.add_argument("--list-categories", action="store_true",
                        help="Lister toutes les categories")
    parser.add_argument("--interactive", action="store_true",
                        help="Mode interactif")

    args = parser.parse_args()

    if args.list_categories:
        list_all_categories()
    elif args.interactive:
        interactive_search()
    elif args.category:
        get_articles_by_category(
            args.category,
            args.subcategory,
            args.limit,
            args.format
        )
    else:
        # Mode interactif par défaut si aucun argument
        interactive_search()


if __name__ == "__main__":
    main()
