import time
import cloudscraper
import json
import re

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1424838729272655938/xcXUXdPipAQO41z8m92st7th0krihjIlcsRNJTbhEv2x0vg2EVjR1GWvqdEgRCxhThQO"
MAX_PRICE = 1000
CATALOG_ID = 257  # Pantalons homme
POLL_INTERVAL = 10  # secondes

scraper = cloudscraper.create_scraper()

def get_items_from_html(catalog_id, max_price):
    url = (
        f"https://www.vinted.fr/vetements?catalog[]={catalog_id}"
        f"&order=newest_first&price_to={max_price}&currency=EUR"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.vinted.fr/",
    }

    try:
        response = scraper.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[!] Erreur HTTP {response.status_code} sur la page Vinted")
            return []

        html = response.text

        # **Ajoute cette ligne pour sauver la page HTML dans un fichier**
        with open("page_vinted.html", "w", encoding="utf-8") as f:
            f.write(html)

        # Extraire le JSON Vinted intégré dans la page
        match = re.search(r'window\.__PRELOADED_STATE__ = ({.*?});', html, re.DOTALL)
        if not match:
            print("[!] JSON Vinted introuvable dans la page")
            return []

        data = json.loads(match.group(1))
        items = list(data.get("catalogItems", {}).get("items", {}).values())
        return items

    except Exception as e:
        print(f"[!] Erreur extraction données : {e}")
        return []


    try:
        response = scraper.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[!] Erreur HTTP {response.status_code} sur la page Vinted")
            return []

        html = response.text

        # 🔽 On sauvegarde le HTML dans un fichier local pour débug
        with open("page_vinted.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[i] HTML sauvegardé dans page_vinted.html")

        # Extraire le JSON Vinted intégré dans la page
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if not match:
            print("[!] JSON Vinted introuvable dans la page")
            return []

        data = json.loads(match.group(1))
        items = list(data.get("catalogItems", {}).get("items", {}).values())
        return items

    except Exception as e:
        print(f"[!] Erreur extraction données : {e}")
        return []

def send_discord_embed(webhook_url, item):
    embed = {
        "embeds": [
            {
                "title": item.get("title", "N/A"),
                "description": f"[Voir l'annonce](https://www.vinted.fr/items/{item.get('id')})",
                "color": 3447003,
                "image": {"url": item.get("photo", "")},
                "fields": [
                    {"name": "Prix", "value": f"{item.get('price', {}).get('amount', '0')} €", "inline": True},
                    {"name": "Marque", "value": item.get("brand_title", "N/A"), "inline": True},
                ],
                "footer": {"text": "Bot Vinted - HTML JSON"},
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        r = scraper.post(webhook_url, json=embed, headers=headers, timeout=10)
        print(f"Discord webhook status: {r.status_code}")
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"[!] Erreur envoi Discord: {e}")
        return False

def main():
    print("[+] Bot Vinted JSON démarré")
    sent_items = set()

    while True:
        items = get_items_from_html(CATALOG_ID, MAX_PRICE)
        print(f"[i] Articles trouvés : {len(items)}")

        for item in items:
            item_id = item.get("id")
            if item_id in sent_items:
                continue

            if send_discord_embed(WEBHOOK_URL, item):
                print(f"[+] Envoyé : {item.get('title')}")
                sent_items.add(item_id)
            else:
                print(f"[!] Échec envoi : {item.get('title')}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
