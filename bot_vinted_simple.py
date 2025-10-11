import time
import json
from playwright.sync_api import sync_playwright

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1424838729272655938/xcXUXdPipAQO41z8m92st7th0krihjIlcsRNJTbhEv2x0vg2EVjR1GWvqdEgRCxhThQO"
MAX_PRICE = 1000
CATALOG_ID = 257  # Pantalons homme
POLL_INTERVAL = 30  # secondes

def send_to_discord(webhook_url, item):
    import requests
    embed = {
        "embeds": [
            {
                "title": item.get("title", "Sans titre"),
                "description": f"[Voir l'annonce](https://www.vinted.fr/items/{item.get('id')})",
                "color": 3447003,
                "image": {"url": item.get("photo")},
                "fields": [
                    {"name": "Prix", "value": f"{item.get('price', {}).get('amount', 0)} €", "inline": True},
                    {"name": "Marque", "value": item.get("brand_title", "N/A"), "inline": True},
                ],
                "footer": {"text": "Bot Vinted - Playwright"},
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(webhook_url, json=embed, headers=headers, timeout=10)
        if r.status_code in (200, 204):
            print(f"[+] Envoyé sur Discord : {item.get('title')}")
            return True
        else:
            print(f"[!] Échec envoi webhook Discord : {r.status_code}")
            return False
    except Exception as e:
        print(f"[!] Exception en envoi Discord : {e}")
        return False

def main():
    print("[+] Bot Vinted démarré avec Playwright")
    sent = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = (
            f"https://www.vinted.fr/vetements?catalog[]={CATALOG_ID}"
            f"&order=newest_first&price_to={MAX_PRICE}&currency=EUR"
        )

        while True:
            page.goto(url)
            time.sleep(5)  # attente que la page charge bien le JS

            # Extrait le contenu JSON via JS dans la page
            data = page.evaluate("() => window.__INITIAL_STATE__ || window.__PRELOADED_STATE__ || null")

            if not data:
                print("[!] Données JSON non trouvées dans la page")
                time.sleep(POLL_INTERVAL)
                continue

            # Les items sont dans data.catalogItems.items
            items = list(data.get("catalogItems", {}).get("items", {}).values()) if data else []

            print(f"[i] Articles trouvés : {len(items)}")

            for item in items:
                item_id = item.get("id")
                if item_id in sent:
                    continue
                if send_to_discord(WEBHOOK_URL, item):
                    sent.add(item_id)

            print(f"[i] Attente {POLL_INTERVAL}s avant prochaine recherche...")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
