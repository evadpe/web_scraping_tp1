# selenium_ffvb_scraper.py
"""
Alternative avec Selenium pour gérer les pages JavaScript
Utilisez cette approche si le scraper Scrapy ne trouve pas assez de données
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time
import re
from urllib.parse import unquote, urljoin

class FFVBSeleniumScraper:
    def __init__(self):
        self.setup_driver()
        self.players_data = []
        
        # Fichier CSV de sortie
        self.csv_file = open('ffvb_players_selenium.csv', 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'nom_joueur', 'numero', 'poste', 'taille', 'poids', 
            'age', 'club', 'url_cv_image', 'url_page', 'methode_extraction'
        ])

    def setup_driver(self):
        """Configure le driver Selenium"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Mode sans interface
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent réaliste
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Driver Selenium initialisé")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Selenium: {e}")
            print("💡 Assurez-vous que ChromeDriver est installé")
            raise

    def scrape_players(self):
        """Méthode principale pour extraire les joueurs"""
        print("🏐 Démarrage du scraping avec Selenium")
        
        # URL de départ
        start_url = "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid=1217&pos=0"
        
        try:
            # 1. Analyser la page de départ
            self.analyze_page(start_url)
            
            # 2. Chercher et naviguer vers d'autres pages de joueurs
            self.find_and_navigate_player_pages()
            
            # 3. Essayer des URLs construites automatiquement
            self.try_constructed_urls()
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
        finally:
            self.cleanup()

    def analyze_page(self, url):
        """Analyse une page pour extraire les informations de joueurs"""
        print(f"🔍 Analyse de: {url}")
        
        self.driver.get(url)
        time.sleep(2)  # Attendre le chargement
        
        # 1. Chercher les images CV
        cv_images = self.extract_cv_images()
        
        # 2. Chercher du contenu textuel
        text_info = self.extract_text_info()
        
        # 3. Chercher les liens de navigation
        nav_links = self.find_navigation_links()
        
        print(f"   📊 Images CV: {len(cv_images)}")
        print(f"   📝 Infos texte: {len(text_info)}")
        print(f"   🔗 Liens navigation: {len(nav_links)}")
        
        return cv_images, text_info, nav_links

    def extract_cv_images(self):
        """Extrait les images CV des joueurs"""
        cv_images = []
        
        try:
            # Chercher toutes les images
            images = self.driver.find_elements(By.TAG_NAME, "img")
            
            for img in images:
                src = img.get_attribute("src")
                if src and ("CV%20JOUEURS" in src or "CV JOUEURS" in src):
                    # Décoder l'URL
                    decoded_src = unquote(src)
                    
                    # Extraire le nom du joueur
                    match = re.search(r'CV\s+JOUEURS/(\d+)\s+([^/]+?)\.png', decoded_src, re.IGNORECASE)
                    
                    if match:
                        numero = match.group(1)
                        nom_complet = match.group(2).strip()
                        
                        player_data = {
                            'nom_joueur': nom_complet,
                            'numero': numero,
                            'url_cv_image': src,
                            'url_page': self.driver.current_url,
                            'methode_extraction': 'cv_image'
                        }
                        
                        cv_images.append(player_data)
                        self.save_player_data(player_data)
                        
                        print(f"   ✅ Joueur trouvé: {nom_complet} (#{numero})")
        
        except Exception as e:
            print(f"   ⚠️ Erreur extraction images: {e}")
        
        return cv_images

    def extract_text_info(self):
        """Extrait les informations textuelles sur les joueurs"""
        text_info = []
        
        try:
            # Chercher dans différents sélecteurs possibles
            selectors = [
                ".articleTexte",
                ".player-info",
                ".joueur-details", 
                "[class*='player']",
                "[class*='joueur']"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Éviter les textes trop courts
                            text_info.append(text)
                except:
                    continue
        
        except Exception as e:
            print(f"   ⚠️ Erreur extraction texte: {e}")
        
        return text_info

    def find_navigation_links(self):
        """Trouve les liens de navigation vers d'autres joueurs"""
        nav_links = []
        
        try:
            # Chercher les liens dans la navigation
            nav_selectors = [
                ".navPart a",
                ".navigation a",
                "a[href*='artid=']",
                "a[href*='pos=']"
            ]
            
            for selector in nav_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute("href")
                        if href and href != self.driver.current_url:
                            nav_links.append(href)
                except:
                    continue
        
        except Exception as e:
            print(f"   ⚠️ Erreur extraction liens: {e}")
        
        return list(set(nav_links))  # Supprimer les doublons

    def find_and_navigate_player_pages(self):
        """Trouve et navigue vers d'autres pages de joueurs"""
        print("🔍 Recherche d'autres pages de joueurs...")
        
        # Liens trouvés sur la page actuelle
        _, _, nav_links = self.analyze_page(self.driver.current_url)
        
        # Naviguer vers chaque lien trouvé
        for link in nav_links[:10]:  # Limiter à 10 pour éviter trop de requêtes
            try:
                print(f"   🔗 Navigation vers: {link}")
                self.analyze_page(link)
                time.sleep(1)  # Pause entre les requêtes
            except Exception as e:
                print(f"   ⚠️ Erreur navigation {link}: {e}")

    def try_constructed_urls(self):
        """Essaie des URLs construites automatiquement"""
        print("🔨 Test d'URLs construites...")
        
        base_pattern = "http://www.ffvb.org/index.php?lvlid=384&dsgtypid=37&artid="
        
        # Tester une plage d'IDs d'articles
        for artid in range(1217, 1230):  # Plage raisonnable
            for pos in range(0, 3):  # Quelques positions
                test_url = f"{base_pattern}{artid}&pos={pos}"
                
                try:
                    print(f"   🧪 Test: {test_url}")
                    self.driver.get(test_url)
                    time.sleep(1)
                    
                    # Vérifier si la page contient des données de joueur
                    cv_images = self.extract_cv_images()
                    if cv_images:
                        print(f"   ✅ Données trouvées sur {test_url}")
                    
                except Exception as e:
                    print(f"   ⚠️ Erreur sur {test_url}: {e}")

    def save_player_data(self, player_data):
        """Sauvegarde les données d'un joueur"""
        self.csv_writer.writerow([
            player_data.get('nom_joueur', ''),
            player_data.get('numero', ''),
            player_data.get('poste', ''),
            player_data.get('taille', ''),
            player_data.get('poids', ''),
            player_data.get('age', ''),
            player_data.get('club', ''),
            player_data.get('url_cv_image', ''),
            player_data.get('url_page', ''),
            player_data.get('methode_extraction', '')
        ])
        
        self.players_data.append(player_data)

    def cleanup(self):
        """Nettoie les ressources"""
        self.csv_file.close()
        self.driver.quit()
        
        print(f"🎉 Scraping terminé! {len(self.players_data)} joueurs trouvés")
        print(f"📄 Résultats sauvegardés dans: ffvb_players_selenium.csv")

def main():
    """Fonction principale"""
    print("🏐 SCRAPER FFVB AVEC SELENIUM")
    print("=" * 40)
    print("📋 Ce scraper utilise Selenium pour gérer le JavaScript")
    print("⚠️  Assurez-vous d'avoir ChromeDriver installé")
    print()
    
    try:
        scraper = FFVBSeleniumScraper()
        scraper.scrape_players()
        return True
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        return False

if __name__ == "__main__":
    main()