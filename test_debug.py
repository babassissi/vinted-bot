import cloudscraper
from bs4 import BeautifulSoup

# --- CONFIG DEBUG ---
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
CATALOG_ID = 257  # pantalon homme
MAX_PRICE = 1000
COUNTRY = "fr"

def get_search_url(catalog_id, price_to, country, search_text="", page=1):
    return (
        f"https://www.vinted.fr/vetements?"
        f"catalog[]={catalog_id}"
        f"&order=newest_first"
        f"&price_to={price_to}"
        f"&currency=EUR"
        f"&country_code={country}"
        f"&search_text={search_text}"
        f"&page={page}"
    ).replace(" ", "")

def parse_items(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.select("a[data-testid='item-box']")

def debug():
    scraper = cloudscraper.create_scraper()
    url = get_search_url(CATALOG_ID, MAX_PRICE, COUNTRY, search_text="", page=1)
    headers = {"User-Agent": USER_AGENT, "Referer": "https://www.vinted.fr/"}
    resp = scraper.get(url, headers=headers, timeout=15)

    print("URL :", url)
    print("Statut HTTP :", resp.status_code)
    text = resp.text
    print("Début du HTML reçu :")
    print(text[:500])
    print("----- Fin aperçu HTML -----\n")

    items = parse_items(text)
    print("Nombre d’éléments avec select('a[data-testid=\"item-box\"]') :", len(items))
    for i, a in enumerate(items[:5]):
        title = a.get("title") or ""
        href = a.get("href")
        print(f"Item {i}: title = {title}, href = {href}")

if __name__ == "__main__":
    debug()
