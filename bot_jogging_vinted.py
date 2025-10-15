# bot_vinted_fixed.py
import time
import os
import random
from dotenv import load_dotenv
from fake_useragent import UserAgent
import requests
from pyVinted import Vinted
import warnings
warnings.filterwarnings("ignore")

# ---------- CONFIG ---------- #
load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

ALLOWED_BRANDS = [
    "nike", "adidas", "ralph lauren", "c.p company", "carhartt", "stüssy",
    "scuffers", "lacoste", "stone island", "the north face", "asics", "salomon",
    "levis", "corteiz", "ami paris"
]
COUNTRY = "fr"
MAX_PRICE = 1000
CATALOG_ID = 257
POLL_INTERVAL = 20  # Augmenté pour éviter blocage
# ---------------------------- #

ua = UserAgent()

# Initialiser Vinted SANS headers (par défaut)
vinted = Vinted()

# Monkey patch pour injecter les headers dans les requêtes de pyVinted
original_request = requests.Session.get
def custom_get(self, url, **kwargs):
    # Injecter headers anti-detection
    headers = kwargs.get('headers', {})
    headers.update({
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Referer': f'https://www.vinted.{COUNTRY}/',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'X-Requested-With': 'XMLHttpRequest',
    })
    kwargs['headers'] = headers
    
    # Délai aléatoire avant requête
    time.sleep(random.uniform(0.5, 2))
    
    return original_request(self, url, **kwargs)

# Appliquer le patch
requests.Session.get = custom_get

def get_search_url(catalog_id, price_to):
    return (f"https://www.vinted.{COUNTRY}/vetements?"
            f"catalog[]={catalog_id}&order=newest_first&price_to={price_to}&currency=EUR")

def brand_allowed(brand_name, allowed_list):
    if not brand_name:
        return False
    bn = brand_name.lower()
    for b in allowed_list:
        if b.lower() in bn or bn in b.lower():
            return True
    return False

def send_discord_embed(webhook_url, title, item_url, image_url, brand, price):
    embed = {
        "embeds": [{
            "title": "🆕 Nouvel article Vinted",
            "description": f"[Voir l'annonce]({item_url})",
            "color": 3447003,
            "image": {"url": image_url} if image_url else None,
            "fields": [
                {"name": "📝 Titre", "value": title[:100] + "..." if len(title) > 100 else title, "inline": False},
                {"name": "🏷️ Marque", "value": brand or "N/A", "inline": True},
                {"name": "💰 Prix", "value": f"{price} €", "inline": True}
            ],
            "footer": {"text": f"Bot Vinted - {time.strftime('%H:%M:%S')}"}
        }]
    }
    headers = {"Content-Type": "application/json", 'User-Agent': ua.random}
    try:
        r = requests.post(webhook_url, json=embed, headers=headers, timeout=15)
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"[!] Erreur webhook: {e}")
        return False

def main():
    if not WEBHOOK_URL:
        print("[!] WEBHOOK_URL manquant dans .env")
        return

    print("[+] 🚀 Bot Vinted anti-blocage démarré")
    print(f"[i] Catalog: {CATALOG_ID}, Prix max: {MAX_PRICE}€, Intervalle: {POLL_INTERVAL}s")
    seen_items = set()
    consecutive_errors = 0

    while True:
        try:
            # Délai aléatoire
            sleep_time = random.uniform(POLL_INTERVAL, POLL_INTERVAL + 10)
            print(f"[i] ⏳ Attente {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            
            search_url = get_search_url(CATALOG_ID, MAX_PRICE)
            print(f"[i] 🔍 Recherche: {search_url.split('?')[0]}...")
            
            # Recherche avec moins d'items
            items = vinted.items.search(search_url, 10, 1)
            consecutive_errors = 0
            
            print(f"[✓] 📦 {len(items)} articles trouvés")
            
            new_count = 0
            for item in items:
                try:
                    item_id = str(getattr(item, 'id', ''))
                    if not item_id or item_id in seen_items:
                        continue

                    # Prix
                    price_str = str(getattr(item, 'price', '0')).replace('€', '').replace(',', '.')
                    price_num = float(price_str) if price_str else 0
                    if price_num > MAX_PRICE:
                        continue

                    # Marque
                    brand = getattr(item, 'brand_title', '') or getattr(item, 'brand_name', '')
                    if not brand_allowed(brand, ALLOWED_BRANDS):
                        continue

                    print(f"[🆕] {brand} - {getattr(item, 'title', 'N/A')[:50]}... {price_num}€")
                    
                    # Image
                    image_url = (getattr(item, 'photo', '') or 
                               (getattr(item, 'images', [None])[0] if hasattr(item, 'images') else ""))
                    
                    # Webhook
                    sent = send_discord_embed(
                        WEBHOOK_URL,
                        getattr(item, 'title', 'N/A'),
                        getattr(item, 'url', ''),
                        image_url,
                        brand,
                        f"{price_num:.2f}"
                    )
                    
                    if sent:
                        print(f"[✅] Discord envoyé!")
                        new_count += 1
                        seen_items.add(item_id)
                    else:
                        print(f"[❌] Échec Discord")
                    
                    # Délai après envoi
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    print(f"[!] Erreur item: {e}")
                    continue

            if new_count == 0:
                print(f"[i] Aucun nouvel article ({len(seen_items)} vus)")
            print("-" * 50)

        except Exception as e:
            consecutive_errors += 1
            print(f"[!] Erreur: {e}")
            if "403" in str(e):
                print(f"[!] 🚫 403 détecté ({consecutive_errors}/5)")
                if consecutive_errors >= 3:
                    print("[!] Pause 10min...")
                    time.sleep(600)
                    consecutive_errors = 0
                else:
                    time.sleep(120)
            else:
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n[*] Arrêt manuel")
            break

if __name__ == "__main__":
    main()