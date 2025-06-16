# spiders/ffvb_players_spider.py
import scrapy
from itemloaders import ItemLoader
from ffvb_scraper.items import PlayerItem, TeamItem, StaffItem
import re
from urllib.parse import urljoin

class FFVBPlayersSpider(scrapy.Spider):
    name = 'ffvb_players'
    allowed_domains = ['ffvb.org', 'www.ffvb.org']
    
    start_urls = [
        # URL spécifique fournie
        'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0',
        
        # URLs supplémentaires pour les équipes de France
        'http://www.ffvb.org/288-37-1-EQUIPES-DE-FRANCE',
        'http://www.ffvb.org/117-37-1-VOLLEY-BALL',
        'http://www.ffvb.org/282-37-1-BEACH-VOLLEY',
        
        # Collectifs spécifiques
        'http://www.ffvb.org/384-37-1-Le-collectif',  # Équipe masculine
        'http://www.ffvb.org/386-37-1-Le-Collectif',  # Équipe féminine
    ]
    
    def __init__(self):
        self.players_count = 0
        self.teams_count = 0
        self.staff_count = 0

    def parse(self, response):
        """Parse initial des pages d'équipes"""
        self.logger.info(f'🏐 Parsing: {response.url}')
        
        # Extraire les informations de l'équipe
        yield from self.extract_team_info(response)
        
        # Extraire les joueurs de cette page
        yield from self.extract_players(response)
        
        # Extraire le staff
        yield from self.extract_staff(response)
        
        # Suivre les liens vers d'autres équipes
        team_links = response.css('a[href*="collectif"], a[href*="equipe"]::attr(href)').getall()
        for link in team_links:
            yield response.follow(link, self.parse)
        
        # Suivre les liens vers les pages de joueurs individuels
        player_links = response.css('a[href*="joueur"], a[href*="player"]::attr(href)').getall()
        for link in player_links:
            yield response.follow(link, self.parse_player_detail)

    def extract_team_info(self, response):
        """Extraire les informations de l'équipe"""
        loader = ItemLoader(item=TeamItem(), response=response)
        
        # Nom de l'équipe
        team_name = response.css('h1::text, .team-name::text, .equipe-titre::text').get()
        if not team_name:
            # Essayer d'extraire depuis le titre de la page
            team_name = response.css('title::text').get()
            if team_name:
                team_name = team_name.replace('FFvolley', '').strip()
        
        loader.add_value('nom_equipe', team_name)
        loader.add_value('url_source', response.url)
        
        # Déterminer la catégorie
        if 'masculin' in response.url.lower() or 'homme' in (team_name or '').lower():
            loader.add_value('categorie', 'Équipe de France Masculine')
        elif 'feminin' in response.url.lower() or 'femme' in (team_name or '').lower():
            loader.add_value('categorie', 'Équipe de France Féminine')
        elif 'beach' in response.url.lower():
            loader.add_value('categorie', 'Beach Volley')
        elif 'jeune' in response.url.lower():
            loader.add_value('categorie', 'Équipes Jeunes')
        else:
            loader.add_value('categorie', 'Équipe de France')
        
        # Entraîneur
        coach = response.css('.coach::text, .entraineur::text').get()
        if not coach:
            # Chercher dans le texte
            text = ' '.join(response.css('*::text').getall())
            coach_match = re.search(r'(?:entraîneur|coach|sélectionneur)[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)', text, re.IGNORECASE)
            if coach_match:
                coach = coach_match.group(1)
        
        loader.add_value('entraineur', coach)
        
        if team_name:
            self.teams_count += 1
            yield loader.load_item()

    def extract_players(self, response):
        """Extraire les joueurs de la page"""
        # Essayer différents sélecteurs pour les joueurs
        player_selectors = [
            '.player-card',
            '.joueur',
            '.player',
            '.effectif-item',
            '.roster-player',
            'div[class*="player"]',
            'div[class*="joueur"]',
            '.collectif-joueur'
        ]
        
        players_found = []
        for selector in player_selectors:
            players = response.css(selector)
            if players:
                players_found.extend(players)
                break
        
        # Si pas de structure de cartes, chercher dans les tableaux
        if not players_found:
            tables = response.css('table')
            for table in tables:
                rows = table.css('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.css('td')
                    if len(cells) >= 2:  # Au moins nom et prénom
                        players_found.append(row)
        
        # Si toujours rien, essayer d'extraire depuis les listes
        if not players_found:
            lists = response.css('ul, ol')
            for lst in lists:
                items = lst.css('li')
                for item in items:
                    text = item.css('::text').get()
                    if text and any(keyword in text.lower() for keyword in ['joueur', 'player', '#']):
                        players_found.append(item)
        
        # Traiter chaque joueur trouvé
        for player_element in players_found:
            yield from self.extract_single_player(player_element, response)

    def extract_single_player(self, player_element, response):
        """Extraire les données d'un joueur individuel"""
        loader = ItemLoader(item=PlayerItem(), selector=player_element)
        
        # Nom et prénom
        name_text = player_element.css('.name::text, .nom::text, .player-name::text').get()
        if not name_text:
            # Essayer depuis les cellules de tableau
            cells = player_element.css('td::text').getall()
            if cells:
                name_text = ' '.join(cells[:2])  # Supposer que nom et prénom sont dans les 2 premières cellules
            else:
                # Essayer le texte complet
                name_text = player_element.css('::text').get()
        
        if name_text:
            # Séparer nom et prénom
            name_parts = name_text.strip().split()
            if len(name_parts) >= 2:
                loader.add_value('prenom', name_parts[0])
                loader.add_value('nom', ' '.join(name_parts[1:]))
                loader.add_value('nom_complet', name_text)
            else:
                loader.add_value('nom_complet', name_text)
        
        # Numéro de maillot
        numero = player_element.css('.number::text, .numero::text').get()
        if not numero:
            # Chercher un numéro dans le texte
            all_text = ' '.join(player_element.css('::text').getall())
            numero_match = re.search(r'#?(\d{1,2})', all_text)
            if numero_match:
                numero = numero_match.group(1)
        loader.add_value('numero_maillot', numero)
        
        # Poste
        poste = player_element.css('.position::text, .poste::text').get()
        if not poste:
            # Chercher dans le texte des postes courants
            all_text = ' '.join(player_element.css('::text').getall()).lower()
            postes_map = {
                'passeur': 'Passeur',
                'libero': 'Libéro',
                'central': 'Central',
                'attaquant': 'Attaquant',
                'pointu': 'Pointu',
                'réceptionneur': 'Réceptionneur-Attaquant',
                'opposite': 'Attaquant Opposé'
            }
            for key, value in postes_map.items():
                if key in all_text:
                    poste = value
                    break
        loader.add_value('poste', poste)
        
        # Taille
        taille = player_element.css('.height::text, .taille::text').get()
        if not taille:
            all_text = ' '.join(player_element.css('::text').getall())
            taille_match = re.search(r'(\d+m\d+|\d{3}cm|\d+\.\d+m)', all_text)
            if taille_match:
                taille = taille_match.group(1)
        loader.add_value('taille', taille)
        
        # Age/Date de naissance
        age = player_element.css('.age::text, .date-naissance::text').get()
        if not age:
            all_text = ' '.join(player_element.css('::text').getall())
            # Chercher une date de naissance
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', all_text)
            if date_match:
                age = date_match.group(1)
            else:
                # Chercher un âge
                age_match = re.search(r'(\d{2})\s*ans?', all_text)
                if age_match:
                    age = age_match.group(1)
        loader.add_value('age', age)
        
        # Club
        club = player_element.css('.club::text, .team::text').get()
        loader.add_value('club_actuel', club)
        
        # Photo
        photo = player_element.css('img::attr(src)').get()
        if photo:
            loader.add_value('photo_url', urljoin(response.url, photo))
        
        # Équipe (déterminée depuis l'URL)
        if 'masculin' in response.url.lower():
            loader.add_value('equipe', 'Équipe de France Masculine')
        elif 'feminin' in response.url.lower():
            loader.add_value('equipe', 'Équipe de France Féminine')
        elif 'beach' in response.url.lower():
            loader.add_value('equipe', 'Beach Volley France')
        else:
            loader.add_value('equipe', 'Équipe de France')
        
        loader.add_value('url_source', response.url)
        
        # Ne yield que si on a au moins un nom
        if name_text:
            self.players_count += 1
            yield loader.load_item()

    def extract_staff(self, response):
        """Extraire les membres du staff"""
        # Chercher les informations du staff
        staff_sections = response.css('.staff, .encadrement, .coaching-staff')
        
        for section in staff_sections:
            staff_members = section.css('.staff-member, .coach, .member')
            
            for member in staff_members:
                loader = ItemLoader(item=StaffItem(), selector=member)
                
                name = member.css('.name::text, ::text').get()
                if name:
                    name_parts = name.strip().split()
                    if len(name_parts) >= 2:
                        loader.add_value('prenom', name_parts[0])
                        loader.add_value('nom', ' '.join(name_parts[1:]))
                
                fonction = member.css('.function::text, .role::text').get()
                loader.add_value('fonction', fonction)
                
                # Équipe
                if 'masculin' in response.url.lower():
                    loader.add_value('equipe', 'Équipe de France Masculine')
                elif 'feminin' in response.url.lower():
                    loader.add_value('equipe', 'Équipe de France Féminine')
                
                loader.add_value('url_source', response.url)
                
                if name:
                    self.staff_count += 1
                    yield loader.load_item()

    def parse_player_detail(self, response):
        """Parser une page de détail d'un joueur"""
        loader = ItemLoader(item=PlayerItem(), response=response)
        
        # Informations détaillées du joueur
        loader.add_css('nom_complet', 'h1::text')
        loader.add_css('poste', '.position::text')
        loader.add_css('taille', '.height::text')
        loader.add_css('poids', '.weight::text')
        loader.add_css('date_naissance', '.birthdate::text')
        loader.add_css('club_actuel', '.current-club::text')
        loader.add_css('nationalite', '.nationality::text')
        
        # Photo
        photo = response.css('.player-photo img::attr(src)').get()
        if photo:
            loader.add_value('photo_url', urljoin(response.url, photo))
        
        loader.add_value('url_source', response.url)
        
        yield loader.load_item()

    def closed(self, reason):
        """Statistiques finales"""
        self.logger.info(f'🎉 Scraping terminé!')
        self.logger.info(f'📊 Statistiques:')
        self.logger.info(f'   👥 Joueurs: {self.players_count}')
        self.logger.info(f'   🏆 Équipes: {self.teams_count}')
        self.logger.info(f'   👔 Staff: {self.staff_count}')