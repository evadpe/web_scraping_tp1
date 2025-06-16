# quick_test_individual_pages.py
"""
Script de test rapide pour analyser les pages individuelles des joueurs
et identifier quelles données sont disponibles pour le scraping
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin, unquote
import time

class QuickPlayerPageTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.test_results = []

    def test_player_pages(self):
        """Teste plusieurs pages de joueurs pour identifier les patterns de données"""
        print("🔍 TEST RAPIDE - PAGES INDIVIDUELLES JOUEURS")
        print("=" * 50)
        
        # URLs à tester (basé sur le pattern identifié)
        test_urls = [
            "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0",  # Page de base
            "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1218&pos=1",  # Joueur suivant probable
            "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1219&pos=2",  # Autre joueur
            "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1220&pos=3",  # Etc.
            "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1221&pos=4",
        ]
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n🏐 [{i}/{len(test_urls)}] Test: {url}")
            
            try:
                result = self.analyze_single_page(url)
                self.test_results.append(result)
                
                print(f"   ✅ Joueur: {result.get('nom_joueur', 'N/A')}")
                print(f"   📊 Données trouvées: {result.get('data_count', 0)}")
                
                # Pause respectueuse
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        # Analyser les résultats
        self.analyze_results()
        
        # Sauvegarder pour référence
        self.save_results()

    def analyze_single_page(self, url):
        """Analyse une seule page de joueur"""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        result = {
            'url': url,
            'nom_joueur': '',
            'numero': '',
            'image_cv_url': '',
            'data_found': {},
            'links_found': [],
            'tables_found': 0,
            'lists_found': 0,
            'data_count': 0,
            'raw_text': '',
            'navigation_links': []
        }
        
        # 1. Chercher l'image CV et extraire nom/numéro
        cv_info = self.extract_cv_info(soup)
        result.update(cv_info)
        
        # 2. Analyser le contenu textuel
        text_data = self.extract_text_data(soup)
        result['data_found'].update(text_data)
        
        # 3. Analyser les tableaux
        tables_data = self.extract_tables_data(soup)
        result['data_found'].update(tables_data)
        result['tables_found'] = len(soup.find_all('table'))
        
        # 4. Analyser les listes
        lists_data = self.extract_lists_data(soup)
        result['data_found'].update(lists_data)
        result['lists_found'] = len(soup.find_all(['ul', 'ol']))
        
        # 5. Trouver les liens vers stats/autres pages
        links = self.find_related_links(soup, url)
        result['links_found'] = links
        
        # 6. Navigation vers autres joueurs
        nav_links = self.find_navigation_links(soup, url)
        result['navigation_links'] = nav_links
        
        # 7. Texte brut pour analyse
        result['raw_text'] = soup.get_text()[:500]  # Premiers 500 caractères
        
        # Compter les données trouvées
        result['data_count'] = len([v for v in result['data_found'].values() if v])
        
        return result

    def extract_cv_info(self, soup):
        """Extrait les infos depuis l'image CV"""
        cv_info = {}
        
        # Chercher les images CV
        images = soup.find_all('img')
        
        for img in images:
            src = img.get('src', '')
            if 'CV%20JOUEURS' in src or 'CV JOUEURS' in src:
                cv_info['image_cv_url'] = src
                
                # Décoder et extraire nom/numéro
                decoded_src = unquote(src)
                match = re.search(r'CV\s+JOUEURS/(\d+)\s+([^/]+?)\.png', decoded_src, re.IGNORECASE)
                
                if match:
                    cv_info['numero'] = match.group(1)
                    cv_info['nom_joueur'] = match.group(2).strip()
                
                break
        
        return cv_info

    def extract_text_data(self, soup):
        """Extrait des données depuis le texte de la page"""
        data = {}
        
        # Récupérer tout le texte
        text = soup.get_text()
        
        # Patterns de recherche
        patterns = {
            'poste': r'(?:poste|position)[\s:]+([^,\n\r\.]+)',
            'taille': r'(?:taille|height)[\s:]*(\d{1,3})(?:\s*cm)?',
            'poids': r'(?:poids|weight)[\s:]*(\d{2,3})(?:\s*kg)?',
            'age': r'(?:âge|age)[\s:]*(\d{1,2})(?:\s*ans)?',
            'club': r'(?:club|équipe)[\s:]+([^,\n\r\.]+)',
            'selections': r'(?:sélections?|caps?)[\s:]*(\d+)',
            'points': r'(?:points?)[\s:]*(\d+)',
            'matches': r'(?:matches?|rencontres?)[\s:]*(\d+)',
            'victoires': r'(?:victoires?)[\s:]*(\d+)',
            'defaites': r'(?:défaites?)[\s:]*(\d+)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[field] = match.group(1).strip()
        
        return data

    def extract_tables_data(self, soup):
        """Extrait des données depuis les tableaux"""
        data = {}
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    left = cells[0].get_text().strip().lower()
                    right = cells[1].get_text().strip()
                    
                    # Identifier des stats potentielles
                    if any(keyword in left for keyword in ['match', 'point', 'victoire', 'sélection']):
                        # Extraire nombre
                        number = re.search(r'\d+', right)
                        if number:
                            data[f'table_{left.replace(" ", "_")}'] = number.group(0)
        
        return data

    def extract_lists_data(self, soup):
        """Extrait des données depuis les listes"""
        data = {}
        
        lists = soup.find_all(['ul', 'ol'])
        competitions = []
        titres = []
        
        for lst in lists:
            items = lst.find_all('li')
            
            for item in items:
                text = item.get_text().strip()
                
                # Identifier compétitions
                if any(keyword in text.lower() for keyword in [
                    'championnat', 'coupe', 'ligue', 'nations', 'européen', 'mondial'
                ]):
                    competitions.append(text)
                
                # Identifier titres
                if any(keyword in text.lower() for keyword in [
                    'champion', 'médaille', 'vainqueur', 'finaliste'
                ]) and re.search(r'\d{4}', text):  # Année
                    titres.append(text)
        
        if competitions:
            data['competitions'] = competitions[:5]  # Max 5
        if titres:
            data['titres'] = titres[:3]  # Max 3
        
        return data

    def find_related_links(self, soup, base_url):
        """Trouve les liens vers des pages de stats/infos connexes"""
        links = []
        
        all_links = soup.find_all('a', href=True)
        
        keywords = ['stats', 'statistiques', 'resultats', 'palmares', 'performance', 'matches']
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text().strip().lower()
            
            if any(keyword in text for keyword in keywords) or \
               any(keyword in href.lower() for keyword in keywords):
                full_url = urljoin(base_url, href)
                links.append({
                    'url': full_url,
                    'text': link.get_text().strip(),
                    'type': 'stats'
                })
        
        return links[:10]  # Max 10

    def find_navigation_links(self, soup, base_url):
        """Trouve les liens de navigation vers autres joueurs"""
        nav_links = []
        
        # Chercher dans la navigation
        nav_elements = soup.select('.navPart a, .navigation a')
        
        for nav in nav_elements:
            href = nav.get('href')
            if href and ('artid=' in href or 'pos=' in href):
                full_url = urljoin(base_url, href)
                nav_links.append({
                    'url': full_url,
                    'text': nav.get_text().strip()
                })
        
        return nav_links[:5]  # Max 5

    def analyze_results(self):
        """Analyse les résultats de tous les tests"""
        print("\n📊 ANALYSE DES RÉSULTATS")
        print("=" * 30)
        
        if not self.test_results:
            print("❌ Aucun résultat à analyser")
            return
        
        # Statistiques générales
        total_pages = len(self.test_results)
        pages_with_players = sum(1 for r in self.test_results if r.get('nom_joueur'))
        
        print(f"📄 Pages testées: {total_pages}")
        print(f"🏐 Pages avec joueurs: {pages_with_players}")
        
        if pages_with_players == 0:
            print("❌ Aucun joueur trouvé")
            return
        
        # Analyse des types de données trouvées
        all_data_types = set()
        for result in self.test_results:
            all_data_types.update(result['data_found'].keys())
        
        print(f"\n📋 Types de données détectées ({len(all_data_types)}):")
        data_frequency = {}
        
        for data_type in all_data_types:
            count = sum(1 for r in self.test_results if r['data_found'].get(data_type))
            data_frequency[data_type] = count
            percentage = (count / pages_with_players) * 100
            print(f"   {data_type}: {count}/{pages_with_players} ({percentage:.1f}%)")
        
        # Joueurs trouvés
        print(f"\n👥 JOUEURS IDENTIFIÉS:")
        for i, result in enumerate(self.test_results, 1):
            if result.get('nom_joueur'):
                nom = result['nom_joueur']
                numero = result.get('numero', 'N/A')
                data_count = result.get('data_count', 0)
                print(f"   {i}. #{numero} - {nom} ({data_count} données)")
        
        # Liens de navigation trouvés
        nav_count = sum(len(r['navigation_links']) for r in self.test_results)
        print(f"\n🔗 Liens de navigation trouvés: {nav_count}")
        
        # Liens vers stats
        stats_count = sum(len(r['links_found']) for r in self.test_results)
        print(f"📈 Liens vers stats trouvés: {stats_count}")
        
        # Recommandations
        self.generate_recommendations()

    def generate_recommendations(self):
        """Génère des recommandations basées sur l'analyse"""
        print(f"\n💡 RECOMMANDATIONS POUR LE SCRAPING:")
        print("-" * 40)
        
        # Analyser la complétude des données
        avg_data_count = sum(r.get('data_count', 0) for r in self.test_results) / len(self.test_results)
        
        if avg_data_count < 3:
            print("⚠️  PEU DE DONNÉES TEXTUELLES DÉTECTÉES")
            print("   → Priorisez l'extraction OCR des images CV")
            print("   → Les données sont probablement dans les images PNG")
        else:
            print("✅ DONNÉES TEXTUELLES DISPONIBLES")
            print("   → Le scraping HTML classique sera efficace")
        
        # Vérifier les patterns de navigation
        nav_found = any(r['navigation_links'] for r in self.test_results)
        if nav_found:
            print("✅ NAVIGATION ENTRE JOUEURS POSSIBLE")
            print("   → Utilisez les liens de navigation détectés")
        else:
            print("⚠️  NAVIGATION LIMITÉE")
            print("   → Construisez les URLs manuellement (artid séquentiel)")
        
        # Analyser les liens vers stats
        stats_links_found = any(r['links_found'] for r in self.test_results)
        if stats_links_found:
            print("✅ LIENS VERS STATISTIQUES DÉTECTÉS")
            print("   → Suivez ces liens pour données complètes")
        else:
            print("⚠️  PAS DE LIENS STATS ÉVIDENTS")
            print("   → Cherchez dans d'autres sections du site")
        
        # Recommandations techniques
        print(f"\n🔧 APPROCHE TECHNIQUE RECOMMANDÉE:")
        
        if avg_data_count >= 5:
            print("1. 🕷️  Scrapy sera suffisant")
            print("2. 📊 Extraire depuis HTML + tableaux")
            print("3. 🖼️  OCR en complément pour images CV")
        else:
            print("1. 🖼️  OCR prioritaire pour images CV")
            print("2. 🤖 Selenium si contenu dynamique")
            print("3. 🕷️  Scrapy pour navigation entre pages")

    def save_results(self):
        """Sauvegarde les résultats pour référence"""
        filename = 'ffvb_quick_test_results.json'
        
        # Préparer les données pour JSON
        json_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_pages_tested': len(self.test_results),
                'pages_with_players': sum(1 for r in self.test_results if r.get('nom_joueur')),
                'avg_data_per_page': sum(r.get('data_count', 0) for r in self.test_results) / len(self.test_results) if self.test_results else 0
            },
            'detailed_results': self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Résultats sauvegardés: {filename}")

    def test_specific_urls(self, urls):
        """Teste des URLs spécifiques fournies par l'utilisateur"""
        print(f"\n🎯 TEST D'URLS SPÉCIFIQUES ({len(urls)} URLs)")
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Test: {url}")
            
            try:
                result = self.analyze_single_page(url)
                
                print(f"   Joueur: {result.get('nom_joueur', 'Non trouvé')}")
                print(f"   Données: {result.get('data_count', 0)}")
                
                # Afficher les données trouvées
                if result['data_found']:
                    print("   Infos trouvées:")
                    for key, value in result['data_found'].items():
                        if value:
                            print(f"     - {key}: {value}")
                
                self.test_results.append(result)
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🏐 TEST RAPIDE - PAGES INDIVIDUELLES FFVB")
    print("Identification des données disponibles pour scraping")
    print()
    
    tester = QuickPlayerPageTester()
    
    # Choix du mode de test
    print("📋 MODES DE TEST DISPONIBLES:")
    print("1. 🔄 Test automatique (URLs prédéfinies)")
    print("2. 🎯 Test d'URLs spécifiques")
    print("3. 🧪 Test d'une seule URL")
    
    try:
        choice = input("\nChoisissez un mode (1-3): ").strip()
        
        if choice == "1":
            print("\n🔄 Lancement du test automatique...")
            tester.test_player_pages()
        
        elif choice == "2":
            print("\n🎯 Entrez les URLs à tester (une par ligne, ligne vide pour terminer):")
            urls = []
            while True:
                url = input("URL: ").strip()
                if not url:
                    break
                urls.append(url)
            
            if urls:
                tester.test_specific_urls(urls)
                tester.analyze_results()
                tester.save_results()
            else:
                print("❌ Aucune URL fournie")
        
        elif choice == "3":
            url = input("\n🧪 Entrez l'URL à tester: ").strip()
            if url:
                result = tester.analyze_single_page(url)
                
                print(f"\n📊 RÉSULTAT POUR: {url}")
                print("-" * 50)
                print(f"Joueur: {result.get('nom_joueur', 'Non trouvé')}")
                print(f"Numéro: {result.get('numero', 'N/A')}")
                print(f"Image CV: {result.get('image_cv_url', 'Non trouvée')}")
                print(f"Données trouvées: {result.get('data_count', 0)}")
                
                if result['data_found']:
                    print("\nDétail des données:")
                    for key, value in result['data_found'].items():
                        if value:
                            print(f"  - {key}: {value}")
                
                if result['links_found']:
                    print(f"\nLiens vers stats: {len(result['links_found'])}")
                    for link in result['links_found'][:3]:
                        print(f"  - {link['text']}: {link['url']}")
                
                if result['navigation_links']:
                    print(f"\nNavigation: {len(result['navigation_links'])} lien(s)")
            else:
                print("❌ Aucune URL fournie")
        
        else:
            print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

def quick_single_test():
    """Test rapide d'une URL pour debug"""
    url = "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0"
    
    tester = QuickPlayerPageTester()
    result = tester.analyze_single_page(url)
    
    print("🔍 RÉSULTAT DU TEST RAPIDE:")
    print(f"Joueur: {result.get('nom_joueur', 'N/A')}")
    print(f"Données: {result.get('data_count', 0)}")
    print(f"Image CV: {'✅' if result.get('image_cv_url') else '❌'}")
    
    return result

if __name__ == "__main__":
    main()