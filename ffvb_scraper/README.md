# 🏐 Projet Scrapy FFVB - Guide Complet

## 📋 Description du Projet
Ce projet de web scraping analyse le site de la Fédération Française de Volley-Ball (ffvb.org) pour extraire et analyser :
- Les actualités et articles
- Les données de championnats
- Les résultats historiques

**Plus-value analytique** : Corrélations géographiques, évolution temporelle, et insights sur la structure du volley-ball français.

## 🚀 Installation et Lancement Rapide

### Option 1 : Lancement automatique
```bash
python run_project.py
```

### Option 2 : Étape par étape

#### 1. Créer l'environnement
```bash
python -m venv venv_scrapy
source venv_scrapy/bin/activate  # Linux/Mac
# ou
venv_scrapy\Scripts\activate     # Windows
```

#### 2. Installer les dépendances
```bash
pip install scrapy pandas matplotlib seaborn requests beautifulsoup4 numpy
```

#### 3. Créer la structure du projet
```bash
scrapy startproject ffvb_scraper
cd ffvb_scraper
```

#### 4. Copier les fichiers
Copiez les artefacts fournis dans les bons répertoires :
- `items.py` → `ffvb_scraper/items.py`
- `settings.py` → `ffvb_scraper/settings.py`
- `pipelines.py` → `ffvb_scraper/pipelines.py`
- `ffvb_spider.py` → `ffvb_scraper/spiders/ffvb_spider.py`
- `analyze_data.py` → répertoire racine

#### 5. Lancer le scraping
```bash
# Depuis le répertoire ffvb_scraper/
scrapy crawl ffvb
```

#### 6. Analyser les données
```bash
# Retourner au répertoire parent
cd ..
python analyze_data.py
```

## 📁 Structure du Projet
```
projet_ffvb/
├── ffvb_scraper/
│   ├── scrapy.cfg
│   ├── ffvb_scraper/
│   │   ├── __init__.py
│   │   ├── items.py          # Définition des données
│   │   ├── settings.py       # Configuration Scrapy
│   │   ├── pipelines.py      # Traitement des données
│   │   └── spiders/
│   │       └── ffvb_spider.py # Spider principal
├── analyze_data.py           # Script d'analyse
├── run_project.py           # Lancement automatique
└── README.md               # Ce guide
```

## 📊 Données Extraites

### 1. Articles (articles_processed.json)
- Titre, date, contenu
- Catégorie (Beach Volley, Équipe de France, etc.)
- URL source

### 2. Championnats (championships_processed.csv)
- Nom du championnat, année
- Équipes, positions, régions
- Divisions (Nationale 1, 2, 3, etc.)

### 3. Résultats Historiques (historical_processed.json)
- Gagnants par année
- Type de championnat
- Catégories (Homme/Femme)

## 📈 Analyses Générées

### Graphiques Standard
1. **articles_analysis.png** - Répartition des actualités
2. **championships_analysis.png** - Analyse des championnats
3. **historical_analysis.png** - Évolution historique

### Plus-Value Analytique
4. **comparative_analysis.png** - Analyses comparatives :
   - Corrélation succès historique vs couverture médiatique
   - Dominance régionale dans les divisions nationales
   - Évolution de la diversité géographique
   - Tendances saisonnières des actualités

### Rapport HTML
5. **ffvb_analysis_report.html** - Rapport interactif complet

## 🎯 Plus-Value du Projet

### 1. Analyses Géographiques
- Cartographie de la dominance régionale
- Score de performance par région
- Évolution de la diversité territoriale

### 2. Corrélations Temporelles
- Lien entre performances historiques et actualité
- Tendances saisonnières
- Évolution de la couverture médiatique

### 3. Insights Structurels
- Pyramide compétitive du volley français
- Concentration des talents
- Équilibre Beach vs Indoor

## ⚙️ Configuration et Bonnes Pratiques

### Respect du Robots.txt
```python
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
CONCURRENT_REQUESTS = 1
```

### Gestion des Erreurs
- Retry automatique sur les erreurs 5xx
- Logs détaillés
- Validation des données

### Formats de Sortie
- JSON pour données complexes
- CSV pour données tabulaires
- HTML pour le rapport final

## 🔧 Dépannage

### Problèmes Courants

1. **Scrapy non trouvé**
```bash
pip install scrapy
```

2. **Erreur d'encodage**
```bash
# Assurez-vous d'utiliser UTF-8
export PYTHONIOENCODING=utf-8
```

3. **Pas de données extraites**
- Vérifiez la connectivité internet
- Le site peut avoir changé de structure
- Vérifiez les logs Scrapy

4. **Graphiques ne s'affichent pas**
```bash
pip install matplotlib seaborn
# Sur certains systèmes :
sudo apt-get install python3-tk
```

## 📚 Utilisation Pédagogique

### Pour le Rapport Scolaire
1. **Méthodologie** : Expliquez le choix de Scrapy
2. **Défis techniques** : Gestion des sessions, parsing HTML
3. **Éthique** : Respect du robots.txt, délais entre requêtes
4. **Plus-value** : Analyses non disponibles sur le site original

### Améliorations Possibles
- Ajout de données géolocalisées
- Intégration avec des APIs externes
- Analyse de sentiment sur les articles
- Prédictions basées sur les tendances

## 📞 Support
Pour toute question sur ce projet :
1. Vérifiez les logs Scrapy
2. Consultez la documentation officielle : https://docs.scrapy.org/
3. Testez d'abord sur quelques pages avec `DOWNLOAD_DELAY = 5`

---
**Projet réalisé dans un cadre pédagogique - Respecte les bonnes pratiques du web scraping**