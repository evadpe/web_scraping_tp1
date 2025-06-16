# spiders/ffvb_debug_spider.py
import scrapy
import csv
import re
from datetime import datetime

class FFVBDebugSpider(scrapy.Spider):
    name = 'ffvb_debug'
    allowed_domains = ['ffvb.org', 'www.ffvb.org']
    start_urls = [
        'http://www.ffvb.org/',
    ]
    
    def __init__(self):
        # Initialiser le fichier CSV
        self.csv_file = open('ffvb_debug_export.csv', 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        
        # En-têtes du CSV
        self.csv_writer.writerow([
            'type_donnee', 'titre', 'date', 'contenu', 'equipe_gagnant', 
            'position', 'region', 'division', 'categorie', 'url_source', 'date_scraping'
        ])
        
        self.scraped_count = 0
        self.debug_info = []

    def closed(self, reason):
        """Fermer le fichier CSV et afficher les infos de debug"""
        self.csv_file.close()
        self.logger.info(f'🎉 Debug terminé! {self.scraped_count} lignes exportées')
        
        # Écrire un fichier de debug
        with open('debug_info.txt', 'w', encoding='utf-8') as f:
            f.write("=== DEBUG SCRAPY FFVB ===\n\n")
            for info in self.debug_info:
                f.write(f"{info}\n")

    def parse(self, response):
        """Parse avec debug détaillé"""
        self.debug_info.append(f"🌐 ACCÈS À: {response.url}")
        self.debug_info.append(f"📊 STATUS CODE: {response.status}")
        self.debug_info.append(f"📏 TAILLE CONTENU: {len(response.text)} caractères")
        
        # Sauvegarder le HTML pour inspection
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        self.debug_info.append("💾 HTML sauvé dans: page_source.html")
        
        # Test 1: Recherche d'articles avec plusieurs sélecteurs
        self.debug_info.append("\n=== TEST SÉLECTEURS ARTICLES ===")
        
        selectors_to_test = [
            'div.article',
            '.news-item', 
            '.actualite',
            '.actu-item',
            'article',
            '.post',
            '.entry',
            'div[class*="article"]',
            'div[class*="news"]',
            'div[class*="actu"]'
        ]
        
        for selector in selectors_to_test:
            elements = response.css(selector)
            self.debug_info.append(f"  {selector}: {len(elements)} éléments trouvés")
            
            if len(elements) > 0:
                # Examiner le premier élément
                first_element = elements[0]
                text_content = first_element.get()[:200] + "..." if len(first_element.get()) > 200 else first_element.get()
                self.debug_info.append(f"    Premier élément: {text_content}")
        
        # Test 2: Recherche de titres
        self.debug_info.append("\n=== TEST SÉLECTEURS TITRES ===")
        
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.title', '.headline', '.post-title',
            'h1::text', 'h2::text', 'h3::text'
        ]
        
        for selector in title_selectors:
            elements = response.css(selector)
            self.debug_info.append(f"  {selector}: {len(elements)} éléments trouvés")
            
            if len(elements) > 0:
                # Prendre les 3 premiers titres
                for i, elem in enumerate(elements[:3]):
                    title_text = elem.css('::text').get() or elem.get()
                    if title_text:
                        title_text = title_text.strip()[:100]
                        self.debug_info.append(f"    Titre {i+1}: {title_text}")
        
        # Test 3: Recherche de liens
        self.debug_info.append("\n=== TEST LIENS ===")
        
        all_links = response.css('a::attr(href)').getall()
        self.debug_info.append(f"  Total liens trouvés: {len(all_links)}")
        
        # Liens vers actualités/news
        news_links = [link for link in all_links if any(word in link.lower() for word in ['actualite', 'news', 'article'])]
        self.debug_info.append(f"  Liens actualités: {len(news_links)}")
        
        # Liens vers championnats
        championship_links = [link for link in all_links if 'championnat' in link.lower()]
        self.debug_info.append(f"  Liens championnats: {len(championship_links)}")
        
        # Test 4: Extraction forcée de contenu
        self.debug_info.append("\n=== EXTRACTION FORCÉE ===")
        
        # Essayer d'extraire n'importe quel contenu textuel
        all_text = response.css('body *::text').getall()
        meaningful_text = [text.strip() for text in all_text if text.strip() and len(text.strip()) > 10]
        
        self.debug_info.append(f"  Éléments texte trouvés: {len(meaningful_text)}")
        
        # Créer des entrées de test avec ce qu'on trouve
        if meaningful_text:
            for i, text in enumerate(meaningful_text[:5]):  # Prendre les 5 premiers
                self.write_csv_row(
                    type_donnee='Test_Extraction',
                    titre=f'Contenu trouvé {i+1}',
                    contenu=text[:200],  # Limiter à 200 caractères
                    url_source=response.url
                )
        
        # Test 5: Vérification robots.txt
        robots_url = response.urljoin('/robots.txt')
        self.debug_info.append(f"\n=== ROBOTS.TXT ===")
        self.debug_info.append(f"  URL: {robots_url}")
        
        yield scrapy.Request(robots_url, callback=self.parse_robots, dont_filter=True)
        
        # Essayer de suivre quelques liens trouvés
        if news_links:
            for link in news_links[:2]:  # Seulement 2 pour le test
                yield response.follow(link, self.parse_test_page)

    def parse_robots(self, response):
        """Analyser le robots.txt"""
        self.debug_info.append(f"📋 ROBOTS.TXT STATUS: {response.status}")
        if response.status == 200:
            robots_content = response.text[:500]  # Premiers 500 caractères
            self.debug_info.append(f"📋 ROBOTS.TXT CONTENU: {robots_content}")

    def parse_test_page(self, response):
        """Test sur une page secondaire"""
        self.debug_info.append(f"\n🔗 PAGE SECONDAIRE: {response.url}")
        self.debug_info.append(f"📊 STATUS: {response.status}")
        
        # Essayer d'extraire du contenu de cette page
        titles = response.css('h1::text, h2::text, h3::text').getall()
        if titles:
            self.debug_info.append(f"📰 Titres trouvés sur cette page: {len(titles)}")
            for title in titles[:3]:
                self.write_csv_row(
                    type_donnee='Article_Test',
                    titre=title.strip(),
                    url_source=response.url
                )

    def write_csv_row(self, type_donnee='', titre='', date='', contenu='', equipe_gagnant='', 
                      position='', region='', division='', categorie='', url_source=''):
        """Écrire une ligne dans le fichier CSV"""
        self.csv_writer.writerow([
            type_donnee, titre or '', date or '', contenu or '', equipe_gagnant or '',
            position or '', region or '', division or '', categorie or '',
            url_source or '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
        self.scraped_count += 1
        self.debug_info.append(f"✍️  Ligne CSV écrite: {type_donnee} - {titre[:50]}")