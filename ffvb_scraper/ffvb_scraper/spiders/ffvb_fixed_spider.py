# spiders/ffvb_fixed_spider.py
import scrapy
import csv
import re
from urllib.parse import urljoin, unquote

class FFVBFixedSpider(scrapy.Spider):
    name = 'ffvb_fixed'
    allowed_domains = ['ffvb.org', 'www.ffvb.org']
    
    # URL de base - page du collectif masculin
    start_urls = [
        'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0',
    ]
    
    def __init__(self):
        self.csv_file = open('ffvb_players_fixed.csv', 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'nom_joueur', 'numero', 'poste', 'url_cv_image', 
            'url_page_joueur', 'type_page', 'source_url'
        ])
        self.players_found = 0

    def closed(self, reason):
        self.csv_file.close()
        self.logger.info(f'🎉 Extraction terminée! {self.players_found} joueurs trouvés')

    def parse(self, response):
        """Parse la page principale et cherche les joueurs"""
        self.logger.info(f'🔍 Analyse de la page: {response.url}')
        
        # 1. Extraire les images CV des joueurs depuis cette page
        cv_images = self.extract_player_cv_images(response)
        
        # 2. Chercher les liens de navigation vers d'autres joueurs
        navigation_links = self.find_player_navigation_links(response)
        
        # 3. Chercher des liens vers d'autres pages de joueurs dans le menu/contenu
        other_player_links = self.find_other_player_pages(response)
        
        # 4. Suivre tous les liens trouvés
        for link in navigation_links + other_player_links:
            yield response.follow(link, self.parse_player_page)
            
        self.logger.info(f'📊 Résumé page actuelle:')
        self.logger.info(f'   - Images CV: {len(cv_images)}')
        self.logger.info(f'   - Liens navigation: {len(navigation_links)}')
        self.logger.info(f'   - Autres liens joueurs: {len(other_player_links)}')

    def extract_player_cv_images(self, response):
        """Extrait les images CV des joueurs de la page actuelle"""
        cv_images = []
        
        # Chercher toutes les images avec le pattern CV JOUEURS
        images = response.css('img::attr(src)').getall()
        
        for img_src in images:
            if 'CV%20JOUEURS' in img_src or 'CV JOUEURS' in img_src:
                # Décoder l'URL pour extraire le nom
                decoded_src = unquote(img_src)
                
                # Extraire le nom du joueur depuis le nom de fichier
                # Pattern: /CV JOUEURS/1 Barthélémy Chinenyeze.png
                match = re.search(r'CV\s+JOUEURS/(\d+)\s+([^/]+?)\.png', decoded_src, re.IGNORECASE)
                
                if match:
                    numero = match.group(1)
                    nom_complet = match.group(2).strip()
                    
                    self.csv_writer.writerow([
                        nom_complet, numero, '', img_src, 
                        response.url, 'cv_image', response.url
                    ])
                    
                    cv_images.append({
                        'nom': nom_complet,
                        'numero': numero,
                        'image_url': img_src
                    })
                    
                    self.players_found += 1
                    self.logger.info(f'✅ Joueur trouvé: {nom_complet} (#{numero})')
        
        return cv_images

    def find_player_navigation_links(self, response):
        """Trouve les liens de navigation vers d'autres joueurs"""
        nav_links = []
        
        # Chercher dans la navigation de la page
        nav_elements = response.css('.navPart a::attr(href)').getall()
        
        for link in nav_elements:
            if link and ('artid=' in link or 'pos=' in link):
                full_url = urljoin(response.url, link)
                nav_links.append(full_url)
                self.logger.info(f'🔗 Lien navigation trouvé: {link}')
        
        return nav_links

    def find_other_player_pages(self, response):
        """Cherche d'autres liens vers des pages de joueurs"""
        player_links = []
        
        # Chercher tous les liens qui pourraient mener à des joueurs
        all_links = response.css('a::attr(href)').getall()
        
        for link in all_links:
            if link and any(keyword in link.lower() for keyword in [
                'collectif', 'joueur', 'player', 'equipe', 'team'
            ]):
                # Éviter les doublons et les liens externes
                if link.startswith('/') or 'ffvb.org' in link:
                    full_url = urljoin(response.url, link)
                    if full_url not in player_links:
                        player_links.append(full_url)
        
        # Construire manuellement des URLs basées sur le pattern observé
        # Si on est sur artid=1217&pos=0, essayer d'autres positions
        base_pattern = 'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid='
        
        # Essayer différents artid (probablement séquentiels pour chaque joueur)
        for artid in range(1217, 1240):  # Tester une plage raisonnable
            for pos in range(0, 5):  # Tester différentes positions
                test_url = f'{base_pattern}{artid}&pos={pos}'
                if test_url != response.url:  # Éviter la page actuelle
                    player_links.append(test_url)
        
        return player_links[:20]  # Limiter pour éviter trop de requêtes

    def parse_player_page(self, response):
        """Parse une page individuelle de joueur"""
        self.logger.info(f'🏐 Analyse page joueur: {response.url}')
        
        # Extraire les images CV de cette page
        cv_images = self.extract_player_cv_images(response)
        
        # Chercher du texte descriptif sur le joueur
        player_info = self.extract_player_text_info(response)
        
        # Continuer la navigation si des liens sont trouvés
        nav_links = self.find_player_navigation_links(response)
        for link in nav_links:
            yield response.follow(link, self.parse_player_page)

    def extract_player_text_info(self, response):
        """Extrait les informations textuelles sur le joueur"""
        # Chercher dans le contenu de l'article
        article_content = response.css('.articleTexte *::text').getall()
        
        # Chercher dans le titre de la page
        page_title = response.css('title::text').get()
        
        # Chercher dans les métadonnées
        meta_content = response.css('meta[name="description"]::attr(content)').get()
        
        # Chercher des informations structurées (si elles existent)
        structured_info = {}
        
        # Pattern pour extraire des infos comme "Taille: 195cm", "Poste: Central", etc.
        all_text = ' '.join(article_content) if article_content else ''
        
        info_patterns = {
            'taille': r'(?:taille|height):\s*(\d+)(?:\s*cm)?',
            'poids': r'(?:poids|weight):\s*(\d+)(?:\s*kg)?',
            'poste': r'(?:poste|position):\s*([^,\n]+)',
            'age': r'(?:age|âge):\s*(\d+)',
            'club': r'(?:club|équipe):\s*([^,\n]+)'
        }
        
        for key, pattern in info_patterns.items():
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                structured_info[key] = match.group(1).strip()
        
        return structured_info