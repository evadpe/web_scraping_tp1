import json
import re
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class BDMScraper:
    """Scraper for Blog du Moderateur articles."""

    def __init__(self):
        """Initialize the scraper with base configuration."""
        self.base_url = "https://www.blogdumoderateur.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'),
            'Accept': ('text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,*/*;q=0.8'),
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def get_homepage_articles(self):
        """
        Retrieve article links from the homepage.

        Returns:
            list: List of article URLs found on the homepage.
        """
        try:
            print(f"Recuperation de la page d'accueil: {self.base_url}")
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            article_links = set()

            # Strategy 1: Find article elements
            articles = soup.find_all('article')
            print(f"{len(articles)} elements <article> trouves")

            for article in articles:
                links = article.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if self._is_article_link(href):
                        full_url = urljoin(self.base_url, href)
                        article_links.add(full_url)

            # Strategy 2: Find all links that look like articles
            all_links = soup.find_all('a', href=True)
            print(f"{len(all_links)} liens totaux trouves")

            for link in all_links:
                href = link['href']
                if self._is_article_link(href):
                    full_url = urljoin(self.base_url, href)
                    article_links.add(full_url)

            # Strategy 3: Find specific patterns (common classes)
            pattern = re.compile(r'(article|post|entry|card|item)', re.I)
            potential_containers = soup.find_all(['div', 'section'],
                                                 class_=pattern)

            for container in potential_containers:
                links = container.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if self._is_article_link(href):
                        full_url = urljoin(self.base_url, href)
                        article_links.add(full_url)

            article_links = list(article_links)
            print(f"{len(article_links)} liens d'articles uniques trouves")

            # Display some examples
            for i, link in enumerate(article_links[:5]):
                print(f"  {i+1}. {link}")

            return article_links

        except requests.RequestException as e:
            print(f"Erreur lors de la recuperation de la page: {e}")
            return []

    def _is_article_link(self, href):
        """
        Determine if a link appears to be an article.

        Args:
            href (str): The href attribute to check.

        Returns:
            bool: True if the link appears to be an article, False otherwise.
        """
        if not href:
            return False

        # Ignore external links
        if (href.startswith('http') and
                'blogdumoderateur.com' not in href):
            return False

        # Ignore links to special pages
        ignore_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/mentions-legales',
            '/politique-confidentialite', '/search',
            '.jpg', '.png', '.gif', '.pdf',
            'mailto:', 'tel:', '#'
        ]

        for pattern in ignore_patterns:
            if pattern in href.lower():
                return False

        # Articles often contain dates or keywords
        article_indicators = [
            r'/20\d{2}/',  # Year in URL
            r'/\d{4}/',    # Year in URL
            r'[\w-]+/$',   # Ends with keyword/
        ]

        for pattern in article_indicators:
            if re.search(pattern, href):
                return True

        # If URL contains at least 2 segments and no suspicious characters
        segments = href.strip('/').split('/')
        suspicious_chars = ['?', '#', '=']
        if (len(segments) >= 2 and
                not any(char in href for char in suspicious_chars)):
            return True

        return False

    def scrape_article(self, url):
        """
        Scrape information from an individual article.

        Args:
            url (str): The URL of the article to scrape.

        Returns:
            dict or None: Article data if successful, None otherwise.
        """
        try:
            print(f"Scraping de l'article: {url}")

            # Delay to respect the server
            time.sleep(1)

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            article_data = {
                'url': url,
                'title': self._extract_title(soup),
                'thumbnail': self._extract_thumbnail(soup, url),
                'subcategory': self._extract_subcategory(soup),
                'summary': self._extract_summary(soup),
                'publish_date': self._extract_publish_date(soup),
                'author': self._extract_author(soup),
                'content': self._extract_content(soup),
                'images': self._extract_images(soup, url),
                'scraped_at': datetime.now().isoformat()
            }

            title_preview = article_data['title'][:50]
            print(f"Article scrape: {title_preview}...")
            return article_data

        except requests.RequestException as e:
            print(f"Erreur lors du scraping de {url}: {e}")
            return None
        except Exception as e:
            print(f"Erreur lors du parsing de {url}: {e}")
            return None

    def _extract_title(self, soup):
        """
        Extract the article title.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            str: The article title or default message.
        """
        title_selectors = [
            'h1',
            '.entry-title',
            '.post-title',
            '.article-title',
            '[class*="title"]',
            'title'
        ]

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                title = title_elem.get_text().strip()
                # Clean the title
                title = re.sub(r'\s+', ' ', title)
                return title

        # Fallback: page title
        if soup.title:
            return soup.title.get_text().strip()

        return "Titre non trouve"

    def _extract_thumbnail(self, soup, url):
        """
        Extract the main thumbnail image.

        Args:
            soup (BeautifulSoup): Parsed HTML content.
            url (str): Base URL for relative links.

        Returns:
            str or None: Thumbnail URL if found, None otherwise.
        """
        # Strategy 1: Meta Open Graph
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return urljoin(url, og_image['content'])

        # Strategy 2: Meta Twitter
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return urljoin(url, twitter_image['content'])

        # Strategy 3: First image in the article
        article_images = soup.find_all('img')
        skip_keywords = ['logo', 'avatar', 'icon']

        for img in article_images:
            src = img.get('src') or img.get('data-src')
            if src and not any(skip in src.lower() for skip in skip_keywords):
                return urljoin(url, src)

        return None

    def _extract_subcategory(self, soup):
        """
        Extrait la sous-catégorie.

        Args:
            soup (BeautifulSoup): Contenu HTML parsé.

        Returns:
            str or None: Sous-catégorie si trouvée, None sinon.
        """
        category_selectors = [
            '.breadcrumb a',
            '.category',
            '.post-category',
            '[class*="category"]',
            '.tag',
            '[rel="category"]'
        ]

        for selector in category_selectors:
            elements = soup.select(selector)
            if elements:
                # Prendre la dernière catégorie (souvent la plus spécifique)
                categories = [
                    elem.get_text(
                        ).strip() for elem in elements if elem.get_text(
                            ).strip()]
                if categories:
                    return categories[-1]

        return None

    def _extract_summary(self, soup):
        """
        Extrait le résumé/extrait de l'article.

        Args:
            soup (BeautifulSoup): Contenu HTML parsé.

        Returns:
            str or None: Résumé si trouvé, None sinon.
        """
        # Stratégie 1: Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()

        # Stratégie 2: Excerpt/summary spécifique
        summary_selectors = [
            '.excerpt',
            '.summary',
            '.lead',
            '.intro',
            '[class*="excerpt"]',
            '[class*="summary"]'
        ]

        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem and summary_elem.get_text().strip():
                return summary_elem.get_text().strip()

        # Stratégie 3: Premier paragraphe du contenu
        content_selectors = '.content, .entry-content, [class*="content"]'
        content_elem = soup.select_one(content_selectors)
        if content_elem:
            first_p = content_elem.find('p')
            if first_p and first_p.get_text().strip():
                return first_p.get_text().strip()

        return None

    def _extract_publish_date(self, soup):
        """
        Extrait la date de publication au format AAAA-MM-JJ.

        Args:
            soup (BeautifulSoup): Contenu HTML parsé.

        Returns:
            str or None: Date de publication si trouvée, None sinon.
        """
        # Stratégie 1: élément time avec datetime
        time_elem = soup.find('time')
        if time_elem and time_elem.get('datetime'):
            try:
                date_str = time_elem['datetime']
                date_obj = self._parse_date(date_str)
                if date_obj:
                    return date_obj.strftime('%Y-%m-%d')
            except Exception:
                pass

        # Stratégie 2: Meta article:published_time
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date and meta_date.get('content'):
            try:
                date_obj = self._parse_date(meta_date['content'])
                if date_obj:
                    return date_obj.strftime('%Y-%m-%d')
            except Exception:
                pass

        # Stratégie 3: Chercher dans le texte
        date_selectors = [
            '.date',
            '.published',
            '[class*="date"]',
            '[class*="time"]'
        ]

        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text().strip()
                date_obj = self._parse_date(date_text)
                if date_obj:
                    return date_obj.strftime('%Y-%m-%d')

        return None

    def _parse_date(self, date_str):
        """
        Parse une chaîne de date en objet datetime.

        Args:
            date_str (str): Chaîne de date à parser.

        Returns:
            datetime or None: Objet datetime parsé ou None si échec.
        """
        # Nettoyer la chaîne
        date_str = re.sub(r'[^\d\-/:. ]', '', date_str).strip()

        # Patterns de date courants
        date_patterns = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M',
        ]

        for pattern in date_patterns:
            try:
                return datetime.strptime(date_str, pattern)
            except ValueError:
                continue

        return None

    def _extract_author(self, soup):
        """
        Extrait l'auteur de l'article.

        Args:
            soup (BeautifulSoup): Contenu HTML parsé.

        Returns:
            str or None: Nom de l'auteur si trouvé, None sinon.
        """
        author_selectors = [
            '.author',
            '.byline',
            '[rel="author"]',
            '[class*="author"]',
            '.post-author'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem and author_elem.get_text().strip():
                author = author_elem.get_text().strip()
                # Nettoyer (enlever "Par", "By", etc.)
                author = re.sub(r'^(par|by|de)\s+', '', author, flags=re.I)
                return author

        return None

    def _extract_content(self, soup):
        """
        Extrait le contenu principal de l'article.

        Args:
            soup (BeautifulSoup): Contenu HTML parsé.

        Returns:
            str or None: Contenu de l'article si trouvé, None sinon.
        """
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content',
            '[class*="content"]',
            'main'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Nettoyer le contenu
                # Supprimer les scripts, styles, etc.
                unwanted_tags = ['script', 'style', 'nav', 'aside']
                for unwanted in content_elem(unwanted_tags):
                    unwanted.decompose()

                # Extraire et nettoyer le texte
                content = content_elem.get_text()
                content = re.sub(r'\n+', '\n', content)
                content = re.sub(r'\s+', ' ', content)
                return content.strip()

        return None

    def _extract_images(self, soup, base_url):
        """
        Extrait toutes les images de l'article avec leurs légendes.

        Args:
            soup (BeautifulSoup): Contenu HTML parsé.
            base_url (str): URL de base pour les liens relatifs.

        Returns:
            dict: Dictionnaire des images avec leurs métadonnées.
        """
        images_dict = {}

        # Chercher dans le contenu principal
        content_selectors = (
            '.entry-content, .post-content,'
            '.article-content, .content, [class*="content"]')
        content_elem = soup.select_one(content_selectors)
        if not content_elem:
            content_elem = soup

        images = content_elem.find_all('img')

        for i, img in enumerate(images):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue

            # URL absolue
            full_url = urljoin(base_url, src)

            # Chercher la légende
            caption = ""

            # Stratégie 1: Texte alternatif
            if img.get('alt'):
                caption = img['alt']

            # Stratégie 2: Attribut title
            elif img.get('title'):
                caption = img['title']

            # Stratégie 3: Figcaption parent
            elif img.find_parent('figure'):
                figcaption = img.find_parent('figure').find('figcaption')
                if figcaption:
                    caption = figcaption.get_text().strip()

            # Stratégie 4: Légende dans un élément proche
            elif img.find_next_sibling(['p', 'div', 'span']):
                next_elem = img.find_next_sibling(['p', 'div', 'span'])
                text = next_elem.get_text().strip()
                if len(text) < 200:  # Probablement une légende
                    caption = text

            images_dict[f"image_{i+1}"] = {
                "url": full_url,
                "caption": caption,
                "order": i + 1
            }

        return images_dict

    def scrape_homepage_articles(self, max_articles=None):
        """
        Scrape tous les articles de la page d'accueil.

        Args:
            max_articles (int, optional): Nombre maximum d'articles à scraper.

        Returns:
            list: Liste des données d'articles scrapés.
        """
        print("Debut du scraping des articles de la page d'accueil")

        # Récupérer les liens des articles
        article_links = self.get_homepage_articles()

        if not article_links:
            print("Aucun article trouve sur la page d'accueil")
            return []

        # Limiter le nombre d'articles si spécifié
        if max_articles:
            article_links = article_links[:max_articles]
            print(f"Limitation a {max_articles} articles")

        scraped_articles = []

        for i, url in enumerate(article_links, 1):
            print(f"\n[{i}/{len(article_links)}] Scraping de l'article...")

            article_data = self.scrape_article(url)

            if article_data:
                scraped_articles.append(article_data)
                title_preview = article_data['title'][:50]
                print(f"Article ajoute: {title_preview}...")
            else:
                print(f"Echec du scraping pour: {url}")

        total_articles = len(scraped_articles)
        total_attempted = len(article_links)
        print(f"\nScraping termine! {total_articles} articles recuperes "
              f"sur {total_attempted} tentes")
        return scraped_articles


def main():
    """Fonction principale pour tester le scraper."""
    scraper = BDMScraper()

    # Scraper les 5 premiers articles de la page d'accueil
    articles = scraper.scrape_homepage_articles(max_articles=5)

    # Afficher un résumé
    print("\n" + "="*60)
    print("RESUME DU SCRAPING")
    print("="*60)

    for i, article in enumerate(articles, 1):
        print(f"\n{i}. Titre: {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Auteur: {article['author'] or 'Non trouve'}")
        print(f"   Date: {article['publish_date'] or 'Non trouvee'}")
        subcategory = article['subcategory'] or 'Non trouvee'
        print(f"   Sous-categorie: {subcategory}")
        summary_preview = (article['summary'] or 'Non trouve')[:100]
        print(f"   Resume: {summary_preview}...")
        print(f"   Images: {len(article['images'])} trouvees")
        content_length = (len(
            article['content']) if article[
                'content'] else 0)
        print(f"   Contenu: {content_length} caracteres")

    # Sauvegarder en JSON pour inspection
    with open('scraped_articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("\nDonnees sauvegardees dans 'scraped_articles.json'")

    return articles


if __name__ == "__main__":
    main()
