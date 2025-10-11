import time
import cloudscraper

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1424838729272655938/xcXUXdPipAQO41z8m92st7th0krihjIlcsRNJTbhEv2x0vg2EVjR1GWvqdEgRCxhThQO"  # Remplace par ton vrai webhook Discord
MAX_PRICE = 1000
COUNTRY = "fr"
CATALOG_ID = 257  # Pantalons homme
POLL_INTERVAL = 10  # secondes

scraper = cloudscraper.create_scraper()

def get_items_api(catalog_id, price_to, country, page=1):
    url = (
        f"https://www.vinted.fr/api/v2/catalog/items"
        f"?catalog_ids[]={catalog_id}&price_to={price_to}&country={country}"
        f"&order=newest_first&page={page}"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://www.vinted.fr/",
    }

    resp = scraper.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"[!] Erreur HTTP {resp.status_code} sur l'API")
        return []
    data = resp.json()
    return data.get("items", [])

def send_discord_embed(webhook_url, item):
    embed = {
        "embeds": [
            {
                "title": item.get("title", "N/A"),
                "description": f"[Voir l'annonce](https://www.vinted.fr/item/{item.get('id')})",
                "color": 3447003,
                "image": {"url": item.get("photos", [{}])[0].get("url_fullxfull", "")},
                "fields": [
                    {"name": "Prix", "value": f"{item.get('price')} €", "inline": True},
                    {"name": "Marque", "value": item.get("brand", "N/A"), "inline": True},
                ],
                "footer": {"text": "Bot Vinted - API"},
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        r = scraper.post(webhook_url, json=embed, headers=headers, timeout=10)
        print(f"Discord webhook status: {r.status_code}")
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"Erreur envoi webhook Discord: {e}")
        return False

def main():
    print("[+] Démarrage du bot Vinted API simplifié avec cloudscraper")
    sent_items = set()
    page = 1
    while True:
        items = get_items_api(CATALOG_ID, MAX_PRICE, COUNTRY, page)
        print(f"[i] Articles trouvés via API : {len(items)}")

        if not items:
            time.sleep(POLL_INTERVAL)
            continue

        for item in items:
            item_id = item.get("id")
            if item_id in sent_items:
                continue

            sent = send_discord_embed(WEBHOOK_URL, item)
            if sent:
                print(f"[+] Envoyé : {item.get('title')}")
                sent_items.add(item_id)
            else:
                print(f"[!] Échec envoi : {item.get('title')}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
