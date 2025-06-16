# run_advanced_scraper.py
import sys
import os
from scrapy.crawler import CrawlerProcess
import csv
from datetime import datetime

def run_advanced_scraper():
    """Lance le scraper avancé pour extraire toutes les données des joueurs"""
    print("🏐 SCRAPER FFVB AVANCÉ - STATS COMPLÈTES DES JOUEURS")
    print("=" * 60)
    print("🎯 Objectifs:")
    print("   ✓ Extraire noms, numéros, postes")
    print("   ✓ Collecter statistiques détaillées")
    print("   ✓ Récupérer historique des compétitions")
    print("   ✓ Naviguer vers pages de stats individuelles")
    print("   ✓ Analyser tableaux de résultats")
    print("   ✓ Extraire informations biographiques")
    print()
    print("📁 Fichiers générés:")
    print("   - ffvb_players_complete.csv (format tableau)")
    print("   - ffvb_players_complete.json (format structuré)")
    print()
    
    # Configuration Scrapy avancée
    settings = {
        'BOT_NAME': 'ffvb_advanced',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # Respectueux du serveur
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        
        # Gestion des erreurs et retry
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'RETRY_PRIORITY_ADJUST': -1,
        
        # Performance optimisée
        'CONCURRENT_REQUESTS': 1,  # Séquentiel pour être respectueux
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        
        # Gestion des redirections
        'REDIRECT_ENABLED': True,
        'REDIRECT_MAX_TIMES': 5,
        
        # Headers plus réalistes
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        
        # Pas de cache pour données fraîches
        'HTTPCACHE_ENABLED': False,
        
        # Durée de vie du scraper
        'CLOSESPIDER_TIMEOUT': 1800,  # 30 minutes max
        'CLOSESPIDER_ITEMCOUNT': 50,  # Max 50 joueurs (sécurité)
        
        # Export en temps réel
        'FEEDS': {
            'ffvb_players_realtime.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
            },
        },
        
        # Middlewares personnalisés
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        },
    }
    
    # Ajouter le répertoire actuel au PYTHONPATH
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    process = CrawlerProcess(settings)
    
    try:
        from ffvb_scraper.spiders.ffvb_advanced_player_scraper import FFVBAdvancedPlayerSpider
        
        print("🕷️  Démarrage du scraper avancé...")
        print("⏳ PATIENCE - Extraction complète en cours...")
        print("📊 Le scraper va :")
        print("   1. Identifier tous les joueurs")
        print("   2. Visiter leur page individuelle")
        print("   3. Chercher leurs pages de statistiques")
        print("   4. Extraire toutes les données disponibles")
        print()
        
        process.crawl(FFVBAdvancedPlayerSpider)
        process.start()
        
        print()
        print("✅ EXTRACTION AVANCÉE TERMINÉE!")
        print("=" * 40)
        
        # Analyser les résultats
        results_summary = analyze_results()
        print(results_summary)
        
        print()
        print("🔍 ANALYSEZ VOS DONNÉES:")
        print("1. 📊 Ouvrez ffvb_players_complete.csv dans Excel/LibreOffice")
        print("2. 🔧 Utilisez ffvb_players_complete.json pour traitement automatisé")
        print("3. 📈 Vérifiez la complétude des statistiques extraites")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez la structure des répertoires:")
        print("   ffvb_scraper/")
        print("   └── spiders/")
        print("       └── ffvb_advanced_player_scraper.py")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def analyze_results():
    """Analyse les résultats de l'extraction"""
    summary = []
    
    try:
        # Analyser le fichier CSV
        if os.path.exists('ffvb_players_complete.csv'):
            with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
                lines = list(f)
                players_count = len(lines) - 1  # -1 pour l'en-tête
            
            summary.append(f"📊 RÉSULTATS D'EXTRACTION:")
            summary.append(f"   └── Joueurs trouvés: {players_count}")
            
            if players_count > 0:
                # Analyser quelques lignes pour voir la complétude
                import csv
                with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    first_player = next(reader, None)
                    
                    if first_player:
                        filled_fields = sum(1 for v in first_player.values() if v.strip())
                        total_fields = len(first_player)
                        completeness = (filled_fields / total_fields) * 100
                        
                        summary.append(f"   └── Complétude des données: {completeness:.1f}%")
                        summary.append(f"   └── Champs remplis: {filled_fields}/{total_fields}")
                        
                        # Afficher quelques données d'exemple
                        summary.append(f"   └── Exemple: {first_player.get('nom_joueur', 'N/A')} "
                                     f"(#{first_player.get('numero', 'N/A')}) - "
                                     f"{first_player.get('poste', 'N/A')}")
        
        # Analyser le fichier JSON
        if os.path.exists('ffvb_players_complete.json'):
            size = os.path.getsize('ffvb_players_complete.json')
            summary.append(f"📄 Fichier JSON: {size:,} bytes")
        
        # Analyser le fichier temps réel
        if os.path.exists('ffvb_players_realtime.jsonl'):
            with open('ffvb_players_realtime.jsonl', 'r', encoding='utf-8') as f:
                realtime_count = sum(1 for line in f)
            summary.append(f"⚡ Extraction temps réel: {realtime_count} éléments")
    
    except Exception as e:
        summary.append(f"⚠️  Erreur analyse résultats: {e}")
    
    return '\n'.join(summary)

def preview_data():
    """Affiche un aperçu des données extraites"""
    print("\n🔍 APERÇU DES DONNÉES EXTRAITES:")
    print("=" * 40)
    
    try:
        if os.path.exists('ffvb_players_complete.csv'):
            import csv
            with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                players = list(reader)
            
            if players:
                print(f"📊 {len(players)} joueur(s) extrait(s)")
                print()
                
                # Afficher les 3 premiers joueurs
                for i, player in enumerate(players[:3], 1):
                    print(f"🏐 JOUEUR {i}:")
                    print(f"   Nom: {player.get('nom_joueur', 'N/A')}")
                    print(f"   Numéro: {player.get('numero', 'N/A')}")
                    print(f"   Poste: {player.get('poste', 'N/A')}")
                    print(f"   Taille: {player.get('taille', 'N/A')}")
                    print(f"   Club: {player.get('club_actuel', 'N/A')}")
                    print(f"   Sélections: {player.get('selections', 'N/A')}")
                    print(f"   Matches: {player.get('matches_joues', 'N/A')}")
                    
                    # Compétitions
                    competitions = player.get('competitions', '')
                    if competitions:
                        comp_list = competitions.split(' | ')[:3]  # 3 premières
                        print(f"   Compétitions: {', '.join(comp_list)}")
                    
                    # Stats
                    if player.get('victoires') and player.get('defaites'):
                        print(f"   Bilan: {player['victoires']}V - {player['defaites']}D")
                    
                    print()
                
                # Statistiques générales
                print("📈 STATISTIQUES GÉNÉRALES:")
                fields_analysis = analyze_field_completeness(players)
                for field, percentage in fields_analysis.items():
                    if percentage > 0:
                        print(f"   {field}: {percentage:.1f}% complété")
            
            else:
                print("❌ Aucun joueur trouvé dans le fichier CSV")
        
        else:
            print("❌ Fichier ffvb_players_complete.csv non trouvé")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'aperçu: {e}")

def analyze_field_completeness(players):
    """Analyse la complétude de chaque champ"""
    if not players:
        return {}
    
    field_stats = {}
    total_players = len(players)
    
    # Champs à analyser
    important_fields = {
        'nom_joueur': 'Nom',
        'numero': 'Numéro', 
        'poste': 'Poste',
        'taille': 'Taille',
        'club_actuel': 'Club',
        'selections': 'Sélections',
        'matches_joues': 'Matches',
        'victoires': 'Victoires',
        'competitions': 'Compétitions'
    }
    
    for field_key, field_name in important_fields.items():
        filled_count = sum(1 for player in players if player.get(field_key, '').strip())
        percentage = (filled_count / total_players) * 100
        field_stats[field_name] = percentage
    
    return field_stats

def create_summary_report():
    """Crée un rapport de synthèse"""
    print("\n📋 CRÉATION DU RAPPORT DE SYNTHÈSE...")
    
    try:
        if not os.path.exists('ffvb_players_complete.csv'):
            print("❌ Fichier de données non trouvé")
            return
        
        import csv
        from datetime import datetime
        
        with open('ffvb_players_complete.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        # Créer le rapport
        report_filename = f'ffvb_rapport_synthese_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("🏐 RAPPORT DE SYNTHÈSE - ÉQUIPE DE FRANCE MASCULINE VOLLEY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Nombre de joueurs: {len(players)}\n\n")
            
            # Analyse par poste
            postes = {}
            for player in players:
                poste = player.get('poste', 'Non défini').strip()
                if poste:
                    postes[poste] = postes.get(poste, 0) + 1
            
            if postes:
                f.write("📊 RÉPARTITION PAR POSTE:\n")
                for poste, count in sorted(postes.items()):
                    f.write(f"   {poste}: {count} joueur(s)\n")
                f.write("\n")
            
            # Liste des joueurs
            f.write("👥 LISTE DES JOUEURS:\n")
            for player in players:
                nom = player.get('nom_joueur', 'N/A')
                numero = player.get('numero', 'N/A')
                poste = player.get('poste', 'N/A')
                club = player.get('club_actuel', 'N/A')
                
                f.write(f"#{numero:>2} - {nom:<25} ({poste:<15}) - {club}\n")
            
            f.write(f"\n📄 Rapport sauvegardé: {report_filename}\n")
        
        print(f"✅ Rapport créé: {report_filename}")
    
    except Exception as e:
        print(f"❌ Erreur création rapport: {e}")

if __name__ == "__main__":
    success = run_advanced_scraper()
    
    if success:
        # Afficher aperçu des données
        preview_data()
        
        # Créer rapport de synthèse
        create_summary_report()
        
        print("\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print("\n💡 PROCHAINES ÉTAPES POSSIBLES:")
        print("1. 🖼️  Extraction OCR des images CV pour plus de détails")
        print("2. 📈 Analyse des tendances et statistiques")
        print("3. 🔄 Automatisation périodique pour mise à jour")
        print("4. 📊 Création de visualisations des données")
    
    else:
        print("\n❌ ÉCHEC DE L'EXTRACTION")
        print("\n🔧 SOLUTIONS POSSIBLES:")
        print("1. Vérifiez votre connexion internet")
        print("2. Vérifiez la structure des répertoires")
        print("3. Installez les dépendances manquantes")
        print("4. Utilisez la version Selenium si problème JavaScript")