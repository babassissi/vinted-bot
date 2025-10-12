# bot_vinted_new.py
import time
import os
from dotenv import load_dotenv
from pyVinted import Vinted
import requests  # For webhook

# ---------- CONFIG ---------- #
load_dotenv()  # Load .env file
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Get from .env: WEBHOOK_URL=your_discord_webhook_here

ALLOWED_BRANDS = [
    "nike", "adidas", "ralph lauren", "c.p company", "carhartt", "stüssy",
    "scuffers", "lacoste", "stone island", "the north face", "asics", "salomon",
    "levis", "corteiz", "ami paris"
]
COUNTRY = "fr"
MAX_PRICE = 1000           # en euros
CATALOG_ID = 257           # ex: 257 = pantalon homme (garde le tien)
POLL_INTERVAL = 6          # secondes entre chaque recherche
# ---------------------------- #

vinted = Vinted()

def get_search_url(catalog_id, price_to):
    # Build the search URL that pyVinted uses to fetch items
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
        "embeds": [
            {
                "title": "Nouvel article Vinted",
                "description": f"[Voir l'annonce]({item_url})",
                "color": 3447003,
                "image": {"url": image_url} if image_url else None,
                "fields": [
                    {"name": "Titre", "value": title or "N/A", "inline": False},
                    {"name": "Marque", "value": brand or "N/A", "inline": True},
                    {"name": "Prix", "value": price or "N/A", "inline": True}
                ],
                "footer": {"text": "Bot Vinted - mis à jour"}
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(webhook_url, json=embed, headers=headers, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False

def main():
    if not WEBHOOK_URL:
        print("[!] WEBHOOK_URL not found in .env file. Add it and restart.")
        return

    print("[+] Démarrage du bot Vinted (nouvelle version - using pyVinted + Webhook)")
    seen_items = set()

    while True:
        try:
            search_url = get_search_url(CATALOG_ID, MAX_PRICE)
            items = vinted.items.search(search_url, 30, 1)
            print(f"[i] Articles trouvés: {len(items)}")

            # Print all fetched items in a simple table for verification (optional - remove if not needed)
            print("\n--- Items Table (All Fetched) ---")
            print(f"{'Title':<60} {'Price':<10} {'URL'}")
            print("-" * 130)
            for item in items:
                title_short = item.title[:57] if len(item.title) > 57 else item.title
                print(f"{title_short:<60} {item.price:<10} {item.url}")
            print("--- End Table ---\n")

            new_count = 0
            for item in items:
                item_id = str(item.id)
                if not item_id:
                    continue

                # Price check - convert to float
                price_num = float(item.price) if item.price else None
                if price_num is not None and price_num > MAX_PRICE:
                    continue

                if item_id in seen_items:
                    continue

                brand = item.brand_title or ""
                if brand_allowed(brand, ALLOWED_BRANDS):
                    print(f"New item: Title: {item.title}, Price: {item.price} {item.currency}, URL: {item.url}")
                    # Send to webhook
                    image_url = item.photos[0].url if hasattr(item, 'photos') and item.photos else ""
                    sent = send_discord_embed(
                        WEBHOOK_URL,
                        item.title,
                        item.url,
                        image_url,
                        brand,
                        f"{item.price} {item.currency}"
                    )
                    if sent:
                        print(f"[+] Sent to webhook!")
                    else:
                        print(f"[!] Failed to send to webhook.")
                    new_count += 1
                    seen_items.add(item_id)

            if new_count == 0:
                print("[i] No new items matching brands this poll.")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("[*] Arrêt manuel reçu, sortie.")
            break
        except Exception as e:
            print(f"[!] Exception: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()