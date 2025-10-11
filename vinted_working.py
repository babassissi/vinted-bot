import time
import json
import requests
import cloudscraper
from bs4 import BeautifulSoup

# ---------- CONFIG ---------- #
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1424838729272655938/xcXUXdPipAQO41z8m92st7th0krihjIlcsRNJTbhEv2x0vg2EVjR1GWvqdEgRCxhThQO"  # <-- Remplace par ton webhook Discord
ALLOWED_BRANDS = [
    "nike", "adidas", "ralph lauren", "c.p company", "carhartt", "stüssy", "jordan",
    "moncler", "lacoste", "stone island", "the north face", "asics", "salomon",
    "levis", "corteiz", "ami paris"
]
COUNTRY = "fr"
MAX_PRICE = 1000           # en euros
CATALOG_ID = 257           # pantalon homme
POLL_INTERVAL = 6          # secondes entre chaque recherche
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# ---------------------------- #

scraper = cloudscraper.create_scraper()

def get_search_url(catalog_id, price_to, country, page=1):
    return (f"https://www.vinted.fr/vetements?catalog[]={catalog_id}"
            f"&order=newest_first&price_to={price_to}&currency=EUR&country_code={country}&page={page}")

def parse_items_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("a[data-testid='item-box']")
    parsed = []
    for a in items:
        try:
            href = a.get("href") or ""
            url = "https://www.vinted.fr" + href if href.startswith("/") else href

            title = a.get("title") or (a.find("h3").get_text(strip=True) if a.find("h3") else "") if a else ""

            img_tag = a.find("img")
            image = img_tag.get("src") or img_tag.get("data-src") if img_tag else ""

            price = "Not found"
            price_tag = a.select_one("[data-testid='price']") or a.select_one("span[itemprop='price']")
            if price_tag:
                price = price_tag.get_text(strip=True)
            else:
                possible = a.get_text(" ", strip=True)
                if "€" in possible:
                    for part in possible.split():
                        if "€" in part:
                            price = part
                            break

            brand = "Not found"
            brand_tag = a.select_one("[data-testid='brand']") or a.select_one(".brand, .item-brand")
            if brand_tag:
                brand = brand_tag.get_text(strip=True)
            else:
                parts = title.split()
                if parts:
                    brand_candidate = parts[0].lower()
                    brand = brand_candidate

            parsed.append({
                "url": url,
                "title": title,
                "image": image,
                "price": price,
                "brand": brand
            })
        except Exception:
            continue
    return parsed

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
                "image": {"url": image_url},
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

def fallback_html_scrape(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.select("a[href*='/items/']"):
        try:
            href = a.get("href")
            url = href if href.startswith("http") else "https://www.vinted.fr" + href
            title = a.get("title") or (a.find("h3").get_text(strip=True) if a.find("h3") else "") if a else ""
        except Exception:
            title = ""
            url = ""
        img = ""
        img_tag = a.find("img")
        if img_tag:
            img = img_tag.get("src") or img_tag.get("data-src") or ""
        results.append({"title": title or "N/A", "price":"N/A", "url":url or "N/A", "image": img, "brand": ""})
    seen = set()
    uniq = []
    for r in results:
        if r["url"] in seen or r["url"] == "N/A":
            continue
        seen.add(r["url"])
        uniq.append(r)
    return uniq

def main():
    print("[+] Démarrage du bot Vinted (nouvelle version)")
    sent_items = set()
    while True:
        try:
            url = get_search_url(CATALOG_ID, MAX_PRICE, COUNTRY, page=1)
            headers = {"User-Agent": USER_AGENT, "Referer": "https://www.vinted.fr/"}
            resp = scraper.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"[!] Erreur HTTP: {resp.status_code} pour {url}")
                time.sleep(POLL_INTERVAL)
                continue

            items = parse_items_from_html(resp.text)
            # si on n’a rien, on peut tenter fallback
            if len(items) == 0:
                items = fallback_html_scrape(resp.text)

            print(f"[i] Articles trouvés: {len(items)}")

            for it in items:
                item_id = it["url"].split("/")[-1] if it["url"] else it["title"]
                brand = it.get("brand", "")
                price_text = it.get("price", "")
                price_num = None
                try:
                    cleaned = "".join(ch for ch in price_text if (ch.isdigit() or ch in ".,"))
                    if cleaned:
                        price_num = float(cleaned.replace(",", "."))
                except Exception:
                    price_num = None

                if brand_allowed(brand, ALLOWED_BRANDS) and (price_num is None or price_num <= MAX_PRICE):
                    if item_id not in sent_items:
                        sent = send_discord_embed(
                            WEBHOOK_URL,
                            it.get("title"),
                            it.get("url"),
                            it.get("image"),
                            brand,
                            it.get("price")
                        )
                        if sent:
                            print(f"[+] Envoyé: {it.get('title')}")
                            sent_items.add(item_id)
                        else:
                            print(f"[!] Échec envoi pour: {it.get('title')}")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("[*] Arrêt manuel reçu, sortie.")
            break
        except Exception as e:
            print(f"[!] Exception: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
