# pipelines.py
import csv
import json
import sqlite3
from datetime import datetime
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import logging

class ValidationPipeline:
    """Pipeline de validation des données"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Validation selon le type d'item
        if adapter.get('nom_complet') or (adapter.get('nom') and adapter.get('prenom')):
            # Item joueur valide
            self.validate_player_item(adapter, spider)
        elif adapter.get('nom_equipe'):
            # Item équipe valide
            self.validate_team_item(adapter, spider)
        elif adapter.get('fonction'):
            # Item staff valide
            self.validate_staff_item(adapter, spider)
        else:
            # Item invalide
            spider.logger.warning(f"Item rejeté - données insuffisantes: {dict(adapter)}")
            raise DropItem("Données insuffisantes")
        
        return item
    
    def validate_player_item(self, adapter, spider):
        """Valider un item joueur"""
        # Nettoyer le numéro de maillot
        if adapter.get('numero_maillot'):
            try:
                numero = int(adapter['numero_maillot'])
                if numero < 1 or numero > 99:
                    adapter['numero_maillot'] = None
            except (ValueError, TypeError):
                adapter['numero_maillot'] = None
        
        # Valider la taille
        if adapter.get('taille'):
            try:
                taille = int(adapter['taille'])
                if taille < 150 or taille > 220:  # Taille raisonnable pour un volleyeur
                    spider.logger.warning(f"Taille suspecte: {taille}cm pour {adapter.get('nom_complet')}")
            except (ValueError, TypeError):
                adapter['taille'] = None
    
    def validate_team_item(self, adapter, spider):
        """Valider un item équipe"""
        if not adapter.get('nom_equipe'):
            raise DropItem("Nom d'équipe manquant")
    
    def validate_staff_item(self, adapter, spider):
        """Valider un item staff"""
        if not adapter.get('fonction'):
            raise DropItem("Fonction du staff manquante")

class CSVExportPipeline:
    """Pipeline d'export CSV"""
    
    def open_spider(self, spider):
        # Fichiers CSV pour chaque type de données
        self.players_file = open('ffvb_players.csv', 'w', newline='', encoding='utf-8')
        self.teams_file = open('ffvb_teams.csv', 'w', newline='', encoding='utf-8')
        self.staff_file = open('ffvb_staff.csv', 'w', newline='', encoding='utf-8')
        
        # Writers CSV
        self.players_writer = csv.writer(self.players_file)
        self.teams_writer = csv.writer(self.teams_file)
        self.staff_writer = csv.writer(self.staff_file)
        
        # En-têtes
        self.players_writer.writerow([
            'nom', 'prenom', 'nom_complet', 'numero_maillot', 'poste', 'taille', 'poids',
            'age', 'date_naissance', 'club_actuel', 'pays_club', 'selections', 'equipe',
            'categorie', 'nationalite', 'lieu_naissance', 'formation', 'photo_url', 'url_source'
        ])
        
        self.teams_writer.writerow([
            'nom_equipe', 'categorie', 'entraineur', 'staff_technique', 'nombre_joueurs', 'url_source'
        ])
        
        self.staff_writer.writerow([
            'nom', 'prenom', 'fonction', 'equipe', 'url_source'
        ])
        
        # Compteurs
        self.players_count = 0
        self.teams_count = 0
        self.staff_count = 0
    
    def close_spider(self, spider):
        self.players_file.close()
        self.teams_file.close()
        self.staff_file.close()
        
        spider.logger.info(f"📁 Fichiers CSV créés:")
        spider.logger.info(f"   👥 ffvb_players.csv: {self.players_count} joueurs")
        spider.logger.info(f"   🏆 ffvb_teams.csv: {self.teams_count} équipes")
        spider.logger.info(f"   👔 ffvb_staff.csv: {self.staff_count} staff")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Déterminer le type d'item et écrire dans le bon fichier
        if adapter.get('nom_complet') or (adapter.get('nom') and adapter.get('prenom')):
            # Item joueur
            self.players_writer.writerow([
                adapter.get('nom', ''),
                adapter.get('prenom', ''),
                adapter.get('nom_complet', ''),
                adapter.get('numero_maillot', ''),
                adapter.get('poste', ''),
                adapter.get('taille', ''),
                adapter.get('poids', ''),
                adapter.get('age', ''),
                adapter.get('date_naissance', ''),
                adapter.get('club_actuel', ''),
                adapter.get('pays_club', ''),
                adapter.get('selections', ''),
                adapter.get('equipe', ''),
                adapter.get('categorie', ''),
                adapter.get('nationalite', ''),
                adapter.get('lieu_naissance', ''),
                adapter.get('formation', ''),
                adapter.get('photo_url', ''),
                adapter.get('url_source', '')
            ])
            self.players_count += 1
            
        elif adapter.get('nom_equipe'):
            # Item équipe
            self.teams_writer.writerow([
                adapter.get('nom_equipe', ''),
                adapter.get('categorie', ''),
                adapter.get('entraineur', ''),
                adapter.get('staff_technique', ''),
                adapter.get('nombre_joueurs', ''),
                adapter.get('url_source', '')
            ])
            self.teams_count += 1
            
        elif adapter.get('fonction'):
            # Item staff
            self.staff_writer.writerow([
                adapter.get('nom', ''),
                adapter.get('prenom', ''),
                adapter.get('fonction', ''),
                adapter.get('equipe', ''),
                adapter.get('url_source', '')
            ])
            self.staff_count += 1
        
        return item

class JSONExportPipeline:
    """Pipeline d'export JSON"""
    
    def open_spider(self, spider):
        self.all_items = []
    
    def close_spider(self, spider):
        # Organiser les données par type
        data = {
            'joueurs': [],
            'equipes': [],
            'staff': [],
            'metadata': {
                'date_extraction': datetime.now().isoformat(),
                'spider': spider.name,
                'total_items': len(self.all_items)
            }
        }
        
        for item in self.all_items:
            adapter = ItemAdapter(item)
            
            if adapter.get('nom_complet') or (adapter.get('nom') and adapter.get('prenom')):
                data['joueurs'].append(dict(adapter))
            elif adapter.get('nom_equipe'):
                data['equipes'].append(dict(adapter))
            elif adapter.get('fonction'):
                data['staff'].append(dict(adapter))
        
        # Sauvegarder en JSON
        with open('ffvb_data_complete.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"📄 Fichier JSON créé: ffvb_data_complete.json")
    
    def process_item(self, item, spider):
        self.all_items.append(item)
        return item

class DatabasePipeline:
    """Pipeline de sauvegarde en base de données SQLite"""
    
    def open_spider(self, spider):
        self.connection = sqlite3.connect('ffvb_database.db')
        self.cursor = self.connection.cursor()
        
        # Créer les tables
        self.create_tables()
    
    def close_spider(self, spider):
        self.connection.close()
        spider.logger.info(f"🗄️  Base de données créée: ffvb_database.db")
    
    def create_tables(self):
        """Créer les tables de la base de données"""
        
        # Table joueurs
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS joueurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                prenom TEXT,
                nom_complet TEXT,
                numero_maillot INTEGER,
                poste TEXT,
                taille INTEGER,
                poids INTEGER,
                age INTEGER,
                date_naissance TEXT,
                club_actuel TEXT,
                pays_club TEXT,
                selections INTEGER,
                equipe TEXT,
                categorie TEXT,
                nationalite TEXT,
                lieu_naissance TEXT,
                formation TEXT,
                photo_url TEXT,
                url_source TEXT,
                date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table équipes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_equipe TEXT,
                categorie TEXT,
                entraineur TEXT,
                staff_technique TEXT,
                nombre_joueurs INTEGER,
                url_source TEXT,
                date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table staff
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                prenom TEXT,
                fonction TEXT,
                equipe TEXT,
                url_source TEXT,
                date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        if adapter.get('nom_complet') or (adapter.get('nom') and adapter.get('prenom')):
            # Insérer joueur
            self.cursor.execute('''
                INSERT INTO joueurs (
                    nom, prenom, nom_complet, numero_maillot, poste, taille, poids,
                    age, date_naissance, club_actuel, pays_club, selections, equipe,
                    categorie, nationalite, lieu_naissance, formation, photo_url, url_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('nom'),
                adapter.get('prenom'),
                adapter.get('nom_complet'),
                adapter.get('numero_maillot'),
                adapter.get('poste'),
                adapter.get('taille'),
                adapter.get('poids'),
                adapter.get('age'),
                adapter.get('date_naissance'),
                adapter.get('club_actuel'),
                adapter.get('pays_club'),
                adapter.get('selections'),
                adapter.get('equipe'),
                adapter.get('categorie'),
                adapter.get('nationalite'),
                adapter.get('lieu_naissance'),
                adapter.get('formation'),
                adapter.get('photo_url'),
                adapter.get('url_source')
            ))
            
        elif adapter.get('nom_equipe'):
            # Insérer équipe
            self.cursor.execute('''
                INSERT INTO equipes (
                    nom_equipe, categorie, entraineur, staff_technique, nombre_joueurs, url_source
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('nom_equipe'),
                adapter.get('categorie'),
                adapter.get('entraineur'),
                adapter.get('staff_technique'),
                adapter.get('nombre_joueurs'),
                adapter.get('url_source')
            ))
            
        elif adapter.get('fonction'):
            # Insérer staff
            self.cursor.execute('''
                INSERT INTO staff (nom, prenom, fonction, equipe, url_source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                adapter.get('nom'),
                adapter.get('prenom'),
                adapter.get('fonction'),
                adapter.get('equipe'),
                adapter.get('url_source')
            ))
        
        self.connection.commit()
        return item

class DuplicateFilterPipeline:
    """Pipeline pour filtrer les doublons"""
    
    def __init__(self):
        self.seen_players = set()
        self.seen_teams = set()
        self.seen_staff = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        if adapter.get('nom_complet') or (adapter.get('nom') and adapter.get('prenom')):
            # Joueur - utiliser nom complet + équipe comme clé unique
            key = f"{adapter.get('nom_complet', '')}-{adapter.get('equipe', '')}"
            if key in self.seen_players:
                spider.logger.debug(f"Joueur dupliqué ignoré: {key}")
                raise DropItem("Joueur dupliqué")
            self.seen_players.add(key)
            
        elif adapter.get('nom_equipe'):
            # Équipe - utiliser nom + catégorie
            key = f"{adapter.get('nom_equipe')}-{adapter.get('categorie', '')}"
            if key in self.seen_teams:
                spider.logger.debug(f"Équipe dupliquée ignorée: {key}")
                raise DropItem("Équipe dupliquée")
            self.seen_teams.add(key)
            
        elif adapter.get('fonction'):
            # Staff - utiliser nom + fonction + équipe
            key = f"{adapter.get('nom', '')}-{adapter.get('prenom', '')}-{adapter.get('fonction')}-{adapter.get('equipe', '')}"
            if key in self.seen_staff:
                spider.logger.debug(f"Staff dupliqué ignoré: {key}")
                raise DropItem("Staff dupliqué")
            self.seen_staff.add(key)
        
        return item

class StatisticsPipeline:
    """Pipeline pour générer des statistiques"""
    
    def open_spider(self, spider):
        self.stats = {
            'players_by_position': {},
            'players_by_team': {},
            'average_height': [],
            'jersey_numbers': set(),
            'clubs': set(),
            'total_players': 0,
            'total_teams': 0,
            'total_staff': 0
        }
    
    def close_spider(self, spider):
        # Calculer les statistiques finales
        if self.stats['average_height']:
            avg_height = sum(self.stats['average_height']) / len(self.stats['average_height'])
            self.stats['average_height'] = round(avg_height, 1)
        else:
            self.stats['average_height'] = 0
        
        # Convertir les sets en listes pour la sérialisation JSON
        self.stats['jersey_numbers'] = sorted(list(self.stats['jersey_numbers']))
        self.stats['clubs'] = sorted(list(self.stats['clubs']))
        
        # Sauvegarder les statistiques
        with open('ffvb_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"📊 Statistiques générées:")
        spider.logger.info(f"   👥 Total joueurs: {self.stats['total_players']}")
        spider.logger.info(f"   🏆 Total équipes: {self.stats['total_teams']}")
        spider.logger.info(f"   👔 Total staff: {self.stats['total_staff']}")
        spider.logger.info(f"   📏 Taille moyenne: {self.stats['average_height']}cm")
        spider.logger.info(f"   🏛️ Clubs différents: {len(self.stats['clubs'])}")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        if adapter.get('nom_complet') or (adapter.get('nom') and adapter.get('prenom')):
            # Statistiques joueurs
            self.stats['total_players'] += 1
            
            # Par poste
            poste = adapter.get('poste', 'Non spécifié')
            self.stats['players_by_position'][poste] = self.stats['players_by_position'].get(poste, 0) + 1
            
            # Par équipe
            equipe = adapter.get('equipe', 'Non spécifiée')
            self.stats['players_by_team'][equipe] = self.stats['players_by_team'].get(equipe, 0) + 1
            
            # Taille moyenne
            if adapter.get('taille'):
                try:
                    taille = int(adapter.get('taille'))
                    if 150 <= taille <= 220:  # Taille raisonnable
                        self.stats['average_height'].append(taille)
                except (ValueError, TypeError):
                    pass
            
            # Numéros de maillot
            if adapter.get('numero_maillot'):
                try:
                    numero = int(adapter.get('numero_maillot'))
                    self.stats['jersey_numbers'].add(numero)
                except (ValueError, TypeError):
                    pass
            
            # Clubs
            if adapter.get('club_actuel'):
                self.stats['clubs'].add(adapter.get('club_actuel'))
                
        elif adapter.get('nom_equipe'):
            self.stats['total_teams'] += 1
            
        elif adapter.get('fonction'):
            self.stats['total_staff'] += 1
        
        return item