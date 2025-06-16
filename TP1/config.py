#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration pour le scraper du Blog du Modérateur
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGODB_CONFIG = {
    'connection_string': os.getenv(
        'MONGODB_URI', 'mongodb://localhost:27017/'),
    'database_name': os.getenv('MONGODB_DB', 'bdm_scraper'),
    'collection_name': 'articles'
}

# Configuration du scraper
SCRAPER_CONFIG = {
    'base_url': 'https://www.blogdumoderateur.com',
    'delay_between_requests': 1.0,  # Délai en secondes
    'max_retries': 3,
    'timeout': 30,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Configuration des logs
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'bdm_scraper.log'
}

# Limites de sécurité
LIMITS = {
    'max_articles_per_session': 100,  # Limite pour éviter la surcharge
    'max_content_length': 1000000,    # 1MB max par article
    'max_images_per_article': 50
}

# Champs requis pour chaque article
REQUIRED_FIELDS = [
    'url',
    'title',
    'thumbnail',
    'subcategory',
    'summary',
    'publish_date',
    'author',
    'content',
    'images'
]

# Configuration de l'interface web (bonus)
WEB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5000,
    'debug': True
}
