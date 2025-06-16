# spiders/ffvb_advanced_player_scraper.py
import scrapy
import csv
import json
import re
from urllib.parse import urljoin, unquote
from datetime import datetime

class FFVBAdvancedPlayerSpider(scrapy.Spider):
    name = 'ffvb_advanced_players'
    allowed_domains = ['ffvb.org', 'www.ffvb.org']
    
    # URL de base - page du collectif masculin
    start_urls = [
        'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0',
    ]
    
    def __init__(self):
        # Fichier CSV détaillé
        self.csv_file = open('ffvb_players_complete.csv', 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 'age', 'date_naissance',
            'club_actuel', 'club_precedent', 'nationalite', 'selections', 'points_totaux',
            'matches_joues', 'victoires', 'defaites', 'ratio_victoires', 'derniere_selection',
            'competitions', 'titres', 'distinctions', 'bio_courte', 'url_cv_image', 
            'url_page_principale', 'urls_stats', 'date_extraction'
        ])
        
        # Fichier JSON pour données structurées
        self.players_data = []
        self.players_found = 0

    def closed(self, reason):
        self.csv_file.close()
        
        # Sauvegarder aussi en JSON
        with open('ffvb_players_complete.json', 'w', encoding='utf-8') as f:
            json.dump(self.players_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f'🎉 Extraction complète terminée! {self.players_found} joueurs avec stats détaillées')

    def parse(self, response):
        """Parse la page principale et trouve tous les joueurs"""
        self.logger.info(f'🔍 Analyse de la page principale: {response.url}')
        
        # 1. Extraire les joueurs de cette page
        players = self.extract_players_from_page(response)
        
        # 2. Pour chaque joueur trouvé, scraper ses données complètes
        for player in players:
            yield self.scrape_player_complete_data(response, player)
        
        # 3. Naviguer vers les autres pages de joueurs
        navigation_links = self.find_all_player_pages(response)
        
        for link in navigation_links:
            yield response.follow(link, self.parse_player_page)

    def extract_players_from_page(self, response):
        """Extrait les joueurs basiques de la page actuelle"""
        players = []
        
        # Chercher les images CV
        images = response.css('img::attr(src)').getall()
        
        for img_src in images:
            if 'CV%20JOUEURS' in img_src or 'CV JOUEURS' in img_src:
                decoded_src = unquote(img_src)
                
                # Extraire nom et numéro
                match = re.search(r'CV\s+JOUEURS/(\d+)\s+([^/]+?)\.png', decoded_src, re.IGNORECASE)
                
                if match:
                    numero = match.group(1)
                    nom_complet = match.group(2).strip()
                    
                    player_basic = {
                        'nom_joueur': nom_complet,
                        'numero': numero,
                        'url_cv_image': img_src,
                        'url_page_principale': response.url
                    }
                    
                    players.append(player_basic)
                    self.logger.info(f'👤 Joueur détecté: {nom_complet} (#{numero})')
        
        return players

    def scrape_player_complete_data(self, response, player_basic):
        """Lance le scraping complet des données d'un joueur"""
        return scrapy.Request(
            url=response.url,
            callback=self.parse_player_detailed,
            meta={'player_basic': player_basic},
            dont_filter=True
        )

    def parse_player_page(self, response):
        """Parse une page individuelle de joueur"""
        self.logger.info(f'🏐 Analyse page joueur: {response.url}')
        
        # Extraire les joueurs de cette page
        players = self.extract_players_from_page(response)
        
        for player in players:
            yield self.scrape_player_complete_data(response, player)
        
        # Continuer la navigation
        nav_links = self.find_navigation_links(response)
        for link in nav_links[:3]:  # Limiter pour éviter boucles infinies
            yield response.follow(link, self.parse_player_page)

    def parse_player_detailed(self, response):
        """Parse les données détaillées d'un joueur"""
        player_basic = response.meta['player_basic']
        self.logger.info(f'📊 Extraction données complètes: {player_basic["nom_joueur"]}')
        
        # Initialiser les données complètes
        player_complete = player_basic.copy()
        player_complete.update({
            'date_extraction': datetime.now().isoformat(),
            'poste': '',
            'taille': '',
            'poids': '',
            'age': '',
            'date_naissance': '',
            'club_actuel': '',
            'club_precedent': '',
            'nationalite': 'France',  # Par défaut équipe de France
            'selections': '',
            'points_totaux': '',
            'matches_joues': '',
            'victoires': '',
            'defaites': '',
            'ratio_victoires': '',
            'derniere_selection': '',
            'competitions': [],
            'titres': [],
            'distinctions': [],
            'bio_courte': '',
            'urls_stats': []
        })
        
        # 1. Extraire informations depuis l'image CV si possible
        cv_info = self.extract_info_from_cv_context(response)
        player_complete.update(cv_info)
        
        # 2. Extraire informations depuis le contenu de la page
        page_info = self.extract_info_from_page_content(response)
        player_complete.update(page_info)
        
        # 3. Chercher des liens vers des pages de statistiques
        stats_links = self.find_stats_links(response, player_complete['nom_joueur'])
        player_complete['urls_stats'] = stats_links
        
        # 4. Suivre les liens de stats pour extraire données détaillées
        for stats_url in stats_links[:3]:  # Limiter à 3 liens par joueur
            yield response.follow(
                stats_url,
                callback=self.parse_player_stats,
                meta={'player_complete': player_complete},
                dont_filter=True
            )
        
        # 5. Sauvegarder les données de base même si pas de stats
        self.save_player_data(player_complete)
        
        yield player_complete

    def extract_info_from_cv_context(self, response):
        """Extrait des infos depuis le contexte autour de l'image CV"""
        info = {}
        
        try:
            # Chercher le contexte autour des images CV
            article_content = response.css('.articleTexte').get()
            
            if article_content:
                # Patterns pour extraire des informations
                patterns = {
                    'poste': r'(?:poste|position)[\s:]+([^,\n\r]+)',
                    'taille': r'(?:taille|height)[\s:]+(\d+)(?:\s*cm)?',
                    'poids': r'(?:poids|weight)[\s:]+(\d+)(?:\s*kg)?',
                    'age': r'(?:âge|age)[\s:]+(\d+)',
                    'club_actuel': r'(?:club|équipe)[\s:]+([^,\n\r]+)',
                    'selections': r'(?:sélections?|caps?)[\s:]+(\d+)',
                    'points_totaux': r'(?:points?)[\s:]+(\d+)'
                }
                
                text_content = re.sub(r'<[^>]+>', ' ', article_content)
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        info[key] = match.group(1).strip()
                        self.logger.info(f'   ✅ {key}: {info[key]}')
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur extraction CV context: {e}')
        
        return info

    def extract_info_from_page_content(self, response):
        """Extrait des informations depuis le contenu général de la page"""
        info = {}
        
        try:
            # Chercher dans tous les textes de la page
            all_text = ' '.join(response.css('*::text').getall())
            
            # Patterns plus larges
            patterns = {
                'bio_courte': r'(?:biographie|présentation|profil)[\s:]+([^.]{20,200})',
                'derniere_selection': r'(?:dernière sélection|last selection)[\s:]+([^,\n]+)',
                'club_precedent': r'(?:ancien club|previous club|ex[- ]club)[\s:]+([^,\n]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    info[key] = match.group(1).strip()
            
            # Chercher des listes de titres/compétitions
            competitions = self.extract_competitions_list(response)
            if competitions:
                info['competitions'] = competitions
            
            titres = self.extract_titres_list(response)
            if titres:
                info['titres'] = titres
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur extraction page content: {e}')
        
        return info

    def extract_competitions_list(self, response):
        """Extrait la liste des compétitions depuis la page"""
        competitions = []
        
        try:
            # Chercher dans des listes ou tableaux
            lists = response.css('ul li, ol li, table tr')
            
            competition_keywords = [
                'championnat', 'coupe', 'ligue', 'nations', 'européen', 
                'mondial', 'olympique', 'jeux', 'tournament'
            ]
            
            for item in lists:
                text = item.css('::text').get()
                if text:
                    text = text.strip()
                    if any(keyword in text.lower() for keyword in competition_keywords):
                        if len(text) > 5 and len(text) < 100:  # Longueur raisonnable
                            competitions.append(text)
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur extraction compétitions: {e}')
        
        return competitions[:10]  # Limiter à 10

    def extract_titres_list(self, response):
        """Extrait la liste des titres/distinctions"""
        titres = []
        
        try:
            # Patterns pour titres
            title_patterns = [
                r'champion[ne]?.*?\d{4}',
                r'médaille.*?\d{4}',
                r'vainqueur.*?\d{4}',
                r'finaliste.*?\d{4}'
            ]
            
            all_text = ' '.join(response.css('*::text').getall())
            
            for pattern in title_patterns:
                matches = re.finditer(pattern, all_text, re.IGNORECASE)
                for match in matches:
                    titre = match.group(0).strip()
                    if titre not in titres and len(titre) < 100:
                        titres.append(titre)
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur extraction titres: {e}')
        
        return titres[:5]  # Limiter à 5

    def find_stats_links(self, response, player_name):
        """Trouve les liens vers les pages de statistiques du joueur"""
        stats_links = []
        
        try:
            # Chercher tous les liens
            all_links = response.css('a::attr(href)').getall()
            
            # Mots-clés pour identifier les pages de stats
            stats_keywords = [
                'stats', 'statistiques', 'resultats', 'results', 
                'performance', 'matches', 'rencontres', 'palmares'
            ]
            
            for link in all_links:
                if link:
                    link_lower = link.lower()
                    if any(keyword in link_lower for keyword in stats_keywords):
                        full_url = urljoin(response.url, link)
                        if full_url not in stats_links:
                            stats_links.append(full_url)
            
            # Chercher des liens contenant le nom du joueur
            if player_name:
                name_parts = player_name.lower().split()
                for link in all_links:
                    if link and any(part in link.lower() for part in name_parts):
                        full_url = urljoin(response.url, link)
                        if full_url not in stats_links:
                            stats_links.append(full_url)
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur recherche liens stats: {e}')
        
        return stats_links[:5]  # Limiter à 5 liens

    def parse_player_stats(self, response):
        """Parse une page de statistiques d'un joueur"""
        player_complete = response.meta['player_complete']
        self.logger.info(f'📈 Extraction stats: {response.url}')
        
        try:
            # Extraire statistiques depuis tableaux
            stats = self.extract_stats_from_tables(response)
            
            # Merger avec les données existantes
            for key, value in stats.items():
                if value and not player_complete.get(key):
                    player_complete[key] = value
            
            # Ajouter l'URL aux sources de stats
            if response.url not in player_complete['urls_stats']:
                player_complete['urls_stats'].append(response.url)
            
            # Re-sauvegarder avec les nouvelles données
            self.save_player_data(player_complete)
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur extraction stats de {response.url}: {e}')
        
        yield player_complete

    def extract_stats_from_tables(self, response):
        """Extrait des statistiques depuis les tableaux de la page"""
        stats = {}
        
        try:
            # Chercher tous les tableaux
            tables = response.css('table')
            
            for table in tables:
                rows = table.css('tr')
                
                for row in rows:
                    cells = row.css('td::text, th::text').getall()
                    cells = [cell.strip() for cell in cells if cell.strip()]
                    
                    if len(cells) >= 2:
                        # Essayer d'identifier des stats
                        left = cells[0].lower()
                        right = cells[1]
                        
                        # Mapping des stats
                        stat_mapping = {
                            'matches': ['matches', 'rencontres', 'games'],
                            'victoires': ['victoires', 'wins', 'gagné'],
                            'defaites': ['défaites', 'defeats', 'perdu'],
                            'points_totaux': ['points', 'pts'],
                            'selections': ['sélections', 'caps', 'selections']
                        }
                        
                        for stat_key, keywords in stat_mapping.items():
                            if any(keyword in left for keyword in keywords):
                                # Extraire nombre depuis right
                                number_match = re.search(r'\d+', right)
                                if number_match:
                                    stats[stat_key] = number_match.group(0)
            
            # Calculer ratio victoires si on a victoires et défaites
            if stats.get('victoires') and stats.get('defaites'):
                try:
                    v = int(stats['victoires'])
                    d = int(stats['defaites'])
                    if v + d > 0:
                        ratio = round(v / (v + d) * 100, 1)
                        stats['ratio_victoires'] = f"{ratio}%"
                except:
                    pass
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur extraction tableaux stats: {e}')
        
        return stats

    def find_all_player_pages(self, response):
        """Trouve toutes les pages de joueurs possibles"""
        player_links = []
        
        # 1. Liens de navigation détectés
        nav_links = self.find_navigation_links(response)
        player_links.extend(nav_links)
        
        # 2. Construction d'URLs basée sur pattern
        base_pattern = 'http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid='
        
        for artid in range(1217, 1240):  # Plage étendue
            for pos in range(0, 5):
                test_url = f'{base_pattern}{artid}&pos={pos}'
                if test_url != response.url:
                    player_links.append(test_url)
        
        return player_links

    def find_navigation_links(self, response):
        """Trouve les liens de navigation"""
        nav_links = []
        
        try:
            # Navigation principale
            nav_elements = response.css('.navPart a::attr(href)').getall()
            
            for link in nav_elements:
                if link and ('artid=' in link or 'pos=' in link):
                    full_url = urljoin(response.url, link)
                    nav_links.append(full_url)
        
        except Exception as e:
            self.logger.warning(f'   ⚠️ Erreur navigation links: {e}')
        
        return nav_links

    def save_player_data(self, player_data):
        """Sauvegarde les données complètes du joueur"""
        try:
            # Convertir listes en strings pour CSV
            competitions_str = ' | '.join(player_data.get('competitions', []))
            titres_str = ' | '.join(player_data.get('titres', []))
            distinctions_str = ' | '.join(player_data.get('distinctions', []))
            urls_stats_str = ' | '.join(player_data.get('urls_stats', []))
            
            # Écrire dans le CSV
            self.csv_writer.writerow([
                player_data.get('nom_joueur', ''),
                player_data.get('numero', ''),
                player_data.get('poste', ''),
                player_data.get('taille', ''),
                player_data.get('poids', ''),
                player_data.get('age', ''),
                player_data.get('date_naissance', ''),
                player_data.get('club_actuel', ''),
                player_data.get('club_precedent', ''),
                player_data.get('nationalite', ''),
                player_data.get('selections', ''),
                player_data.get('points_totaux', ''),
                player_data.get('matches_joues', ''),
                player_data.get('victoires', ''),
                player_data.get('defaites', ''),
                player_data.get('ratio_victoires', ''),
                player_data.get('derniere_selection', ''),
                competitions_str,
                titres_str,
                distinctions_str,
                player_data.get('bio_courte', ''),
                player_data.get('url_cv_image', ''),
                player_data.get('url_page_principale', ''),
                urls_stats_str,
                player_data.get('date_extraction', '')
            ])
            
            # Ajouter aux données JSON
            if player_data not in self.players_data:
                self.players_data.append(player_data)
                self.players_found += 1
        
        except Exception as e:
            self.logger.error(f'❌ Erreur sauvegarde joueur: {e}')