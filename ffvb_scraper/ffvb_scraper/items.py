# items.py
import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
import re

def clean_text(value):
    """Nettoyer le texte"""
    if value:
        # Supprimer les espaces multiples et caractères spéciaux
        value = re.sub(r'\s+', ' ', value.strip())
        # Supprimer les balises HTML
        value = re.sub(r'<[^>]+>', '', value)
        return value
    return ''

def extract_number(value):
    """Extraire un nombre d'une chaîne"""
    if value:
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else None
    return None

def extract_height(value):
    """Extraire la taille en cm"""
    if value:
        # Formats possibles: "1m95", "195cm", "195", "1,95m"
        value = value.replace(',', '.')
        
        # Format 1m95 ou 1.95m
        match = re.search(r'(\d+)[\.,]?(\d+)?m', value)
        if match:
            meters = int(match.group(1))
            cm = int(match.group(2)) if match.group(2) else 0
            return meters * 100 + cm
        
        # Format 195cm ou juste 195
        match = re.search(r'(\d{3})', value)
        if match:
            return int(match.group(1))
            
    return None

def extract_weight(value):
    """Extraire le poids en kg"""
    if value:
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else None
    return None

class PlayerItem(scrapy.Item):
    """Item pour un joueur"""
    # Informations personnelles
    nom = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    prenom = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    nom_complet = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    numero_maillot = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    
    # Caractéristiques physiques
    date_naissance = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    age = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    taille = scrapy.Field(
        input_processor=MapCompose(extract_height),
        output_processor=TakeFirst()
    )
    poids = scrapy.Field(
        input_processor=MapCompose(extract_weight),
        output_processor=TakeFirst()
    )
    
    # Informations sportives
    poste = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    club_actuel = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    pays_club = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Carrière
    selections = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    palmares = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(' | ')
    )
    
    # Métadonnées
    equipe = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    categorie = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    url_source = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    photo_url = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Informations supplémentaires
    nationalite = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    lieu_naissance = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    formation = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )

class TeamItem(scrapy.Item):
    """Item pour une équipe"""
    nom_equipe = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    categorie = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    entraineur = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    staff_technique = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(' | ')
    )
    nombre_joueurs = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    url_source = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )

class StaffItem(scrapy.Item):
    """Item pour un membre du staff"""
    nom = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    prenom = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    fonction = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    equipe = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    url_source = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )