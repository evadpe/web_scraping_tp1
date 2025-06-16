from datetime import datetime
from typing import Dict, List

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError


class MongoDBHandler:
    """Gestionnaire pour les operations MongoDB des articles."""

    def __init__(self, connection_string="mongodb://localhost:27017/",
                 database_name="bdm_scraper"):
        """
        Initialise la connexion MongoDB.

        Args:
            connection_string (str): Chaine de connexion MongoDB.
            database_name (str): Nom de la base de donnees.
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collection = None

        self.connect()

    def connect(self):
        """Etablit la connexion a MongoDB."""
        try:
            print(f"Connexion a MongoDB: {self.connection_string}")
            self.client = MongoClient(self.connection_string)

            # Test de la connexion
            self.client.admin.command('ping')

            self.db = self.client[self.database_name]
            self.collection = self.db.articles

            # Creer les index pour optimiser les recherches
            self.create_indexes()

            print(f"Connexion reussie a la base '{self.database_name}'")

        except ConnectionFailure as e:
            print(f"Erreur de connexion MongoDB: {e}")
            raise
        except Exception as e:
            print(f"Erreur inattendue lors de la connexion: {e}")
            raise

    def create_indexes(self):
        """Cree les index pour optimiser les performances."""
        try:
            # Index sur l'URL (unique) pour eviter les doublons
            self.collection.create_index("url", unique=True)

            # Index pour les recherches par date
            self.collection.create_index("publish_date")

            # Index pour les recherches par auteur
            self.collection.create_index("author")

            # Index pour les recherches par categorie
            self.collection.create_index("subcategory")

            # Index pour les recherches textuelles dans le titre
            text_indexes = [("title", "text"), ("content", "text")]
            self.collection.create_index(text_indexes)

            print("Index MongoDB crees avec succes")

        except Exception as e:
            print(f"Avertissement lors de la creation des index: {e}")

    def save_article(self, article_data: Dict) -> bool:
        """
        Sauvegarde un article dans MongoDB.

        Args:
            article_data (Dict): Donnees de l'article.

        Returns:
            bool: True si sauvegarde avec succes, False sinon.
        """
        try:
            # Ajouter la date de sauvegarde
            article_data['saved_at'] = datetime.now()

            # Tentative d'insertion
            self.collection.insert_one(article_data)

            title = article_data.get('title', 'Sans titre')[:50]
            print(f"Article sauvegarde: {title}...")
            return True

        except DuplicateKeyError:
            url = article_data.get('url', 'URL inconnue')
            print(f"Article deja existant: {url}")
            return False
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False

    def save_articles(self, articles_list: List[Dict]) -> Dict[str, int]:
        """
        Sauvegarde une liste d'articles.

        Args:
            articles_list (List[Dict]): Liste des articles a sauvegarder.

        Returns:
            Dict[str, int]: Statistiques de sauvegarde.
        """
        stats = {
            'total': len(articles_list),
            'saved': 0,
            'duplicates': 0,
            'errors': 0
        }

        print(f"Sauvegarde de {stats['total']} articles...")

        for article in articles_list:
            if self.save_article(article):
                stats['saved'] += 1
            else:
                # Verifier si c'est un doublon ou une erreur
                try:
                    if self.collection.find_one({'url': article.get('url')}):
                        stats['duplicates'] += 1
                    else:
                        stats['errors'] += 1
                except Exception:
                    stats['errors'] += 1

        print("Sauvegarde terminee:")
        print(f"   Sauvegardes: {stats['saved']}")
        print(f"   Doublons: {stats['duplicates']}")
        print(f"   Erreurs: {stats['errors']}")

        return stats

    def get_articles_by_category(self, category: str,
                                 subcategory: str = None) -> List[Dict]:
        """
        Recupere les articles par categorie/sous-categorie.

        Args:
            category (str): Categorie principale.
            subcategory (str, optional): Sous-categorie.

        Returns:
            List[Dict]: Liste des articles trouves.
        """
        try:
            query = {}

            search_term = subcategory if subcategory else category
            query['subcategory'] = {'$regex': search_term, '$options': 'i'}

            articles = list(self.collection.find(query).sort('publish_date',
                                                             DESCENDING))

            category_name = subcategory or category
            print(f"{len(articles)} articles trouves pour la categorie "
                  f"'{category_name}'")

            return articles

        except Exception as e:
            print(f"Erreur lors de la recherche par categorie: {e}")
            return []

    def search_articles(self,
                        title_substring: str = None,
                        author: str = None,
                        category: str = None,
                        subcategory: str = None,
                        date_start: str = None,
                        date_end: str = None,
                        limit: int = None) -> List[Dict]:
        """
        Recherche avancee d'articles.

        Args:
            title_substring (str): Sous-chaine a rechercher dans le titre.
            author (str): Nom de l'auteur.
            category (str): Categorie.
            subcategory (str): Sous-categorie.
            date_start (str): Date de debut (format YYYY-MM-DD).
            date_end (str): Date de fin (format YYYY-MM-DD).
            limit (int): Nombre maximum de resultats.

        Returns:
            List[Dict]: Articles correspondant aux criteres.
        """
        try:
            query = {}

            # Recherche par titre
            if title_substring:
                query['title'] = {'$regex': title_substring, '$options': 'i'}

            # Recherche par auteur
            if author:
                query['author'] = {'$regex': author, '$options': 'i'}

            # Recherche par categorie
            if category:
                query['subcategory'] = {'$regex': category, '$options': 'i'}

            # Recherche par sous-categorie (plus specifique)
            if subcategory:
                query['subcategory'] = {'$regex': subcategory,
                                        '$options': 'i'}

            # Recherche par date
            date_query = {}
            if date_start:
                date_query['$gte'] = date_start
            if date_end:
                date_query['$lte'] = date_end

            if date_query:
                query['publish_date'] = date_query

            print(f"Recherche avec les criteres: {query}")

            # Executer la requete
            cursor = self.collection.find(query).sort('publish_date',
                                                      DESCENDING)

            if limit:
                cursor = cursor.limit(limit)

            articles = list(cursor)

            print(f"{len(articles)} articles trouves")

            return articles

        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []

    def get_all_categories(self) -> List[str]:
        """
        Recupere toutes les categories uniques.

        Returns:
            List[str]: Liste des categories.
        """
        try:
            categories = self.collection.distinct('subcategory')
            # Enlever les valeurs nulles
            categories = [cat for cat in categories if cat]
            print(f"{len(categories)} categories trouvees")
            return sorted(categories)
        except Exception as e:
            print(f"Erreur lors de la recuperation des categories: {e}")
            return []

    def get_all_authors(self) -> List[str]:
        """
        Recupere tous les auteurs uniques.

        Returns:
            List[str]: Liste des auteurs.
        """
        try:
            authors = self.collection.distinct('author')
            # Enlever les valeurs nulles
            authors = [author for author in authors if author]
            print(f"{len(authors)} auteurs trouves")
            return sorted(authors)
        except Exception as e:
            print(f"Erreur lors de la recuperation des auteurs: {e}")
            return []

    def get_statistics(self) -> Dict:
        """
        Recupere les statistiques de la base de donnees.

        Returns:
            Dict: Statistiques de la base.
        """
        try:
            stats = {
                'total_articles': self.collection.count_documents({}),
                'total_categories': len(self.get_all_categories()),
                'total_authors': len(self.get_all_authors()),
                'date_range': self.get_date_range()
            }
            return stats
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {e}")
            return {}

    def get_date_range(self) -> Dict:
        """
        Recupere la plage de dates des articles.

        Returns:
            Dict: Plage de dates avec 'oldest' et 'newest'.
        """
        try:
            # Article le plus ancien
            oldest_query = {'publish_date': {'$ne': None}}
            oldest = self.collection.find(
                oldest_query).sort('publish_date',
                                   ASCENDING).limit(1)
            oldest = list(oldest)

            # Article le plus recent
            newest_query = {'publish_date': {'$ne': None}}
            newest = self.collection.find(
                newest_query).sort('publish_date',
                                   DESCENDING).limit(1)
            newest = list(newest)

            return {
                'oldest': oldest[0]['publish_date'] if oldest else None,
                'newest': newest[0]['publish_date'] if newest else None
            }
        except Exception as e:
            print(f"Erreur lors du calcul de la plage de dates: {e}")
            return {'oldest': None, 'newest': None}

    def close_connection(self):
        """Ferme la connexion MongoDB."""
        if self.client:
            self.client.close()
            print("Connexion MongoDB fermee")


def main():
    """Fonction de test du gestionnaire MongoDB."""
    # Test de connexion
    db_handler = MongoDBHandler()

    # Afficher les statistiques
    stats = db_handler.get_statistics()
    print("\nStatistiques de la base de donnees:")
    print(f"   Articles: {stats.get('total_articles', 0)}")
    print(f"   Categories: {stats.get('total_categories', 0)}")
    print(f"   Auteurs: {stats.get('total_authors', 0)}")

    date_range = stats.get('date_range', {})
    if date_range.get('oldest'):
        oldest = date_range['oldest']
        newest = date_range['newest']
        print(f"   Periode: {oldest} a {newest}")

    # Test de recherche
    print("\nTest de recherche...")
    results = db_handler.search_articles(limit=5)

    for i, article in enumerate(results[:3], 1):
        title = article.get('title', 'Sans titre')[:50]
        print(f"{i}. {title}...")

    db_handler.close_connection()


if __name__ == "__main__":
    main()
