# ffvb_working_spider.py - Version allégée
import scrapy
import re
from urllib.parse import urljoin
from datetime import datetime

class FFVBWorkingSpider(scrapy.Spider):
    name = 'ffvb'
    allowed_domains = ['ffvb.org']
    start_urls = [
        'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0',
        'http://www.ffvb.org/index.php?lvlid=386&dsgtypid=37&artid=1219&pos=0',
    ]
    
    def __init__(self):
        self.players_found = 0
        
    def parse(self, response):
        self.logger.info(f"🏐 Parsing: {response.url}")
        
        equipe_type = 'Équipe de France Masculine' if 'lvlid=384' in response.url else 'Équipe de France Féminine'
        
        # Chercher tous les éléments contenant potentiellement des joueurs
        containers = response.css('div, tr, li, article, section')
        
        for container in containers:
            text_content = ' '.join(container.css('::text').getall())
            
            # Recherche de noms (mots avec majuscules)
            nom_match = re.search(r'\b([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\-']{2,}(?:\s+[A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\-']{2,})+)\b', text_content)
            
            if nom_match:
                nom = nom_match.group(1).strip()
                
                # Éviter les faux positifs
                if any(word in nom.lower() for word in ['équipe', 'france', 'volley', 'beach', 'contact', 'mentions']):
                    continue
                
                player_data = {
                    'nom_joueur': nom,
                    'equipe': equipe_type,
                    'url_source': response.url,
                    'date_extraction': datetime.now().isoformat()
                }
                
                # Chercher le numéro
                numero_match = re.search(r'\b(\d{1,2})\b', text_content)
                if numero_match and 1 <= int(numero_match.group(1)) <= 99:
                    player_data['numero'] = numero_match.group(1)
                
                # Chercher le poste
                postes = ['attaquant', 'passeur', 'central', 'libéro', 'réceptionneur']
                for poste in postes:
                    if poste in text_content.lower():
                        player_data['poste'] = poste.title()
                        break
                
                # Chercher les images
                images = container.css('img::attr(src)').getall()
                for img in images:
                    if 'cv' in img.lower() or 'photo' in img.lower():
                        player_data['url_cv_image'] = urljoin(response.url, img)
                        break
                
                self.players_found += 1
                self.logger.info(f"✅ Joueur: {nom}")
                
                yield player_data
        
        # Chercher d'autres pages
        links = response.css('a::attr(href)').getall()
        for link in links:
            if any(param in link for param in ['artid=', 'pos=', 'joueur']):
                yield response.follow(link, self.parse_player_page, meta={'equipe': equipe_type})
    
    def parse_player_page(self, response):
        self.logger.info(f"👤 Page joueur: {response.url}")
        
        # Extraction simple depuis page joueur
        text = ' '.join(response.css('::text').getall())
        
        # Nom depuis titre
        title = response.css('title::text').get() or response.css('h1::text').get() or ''
        nom_match = re.search(r'([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\s\-']+)', title)
        
        if nom_match:
            yield {
                'nom_joueur': nom_match.group(1).strip(),
                'equipe': response.meta.get('equipe', 'Équipe de France'),
                'url_page_principale': response.url,
                'date_extraction': datetime.now().isoformat()
            }
