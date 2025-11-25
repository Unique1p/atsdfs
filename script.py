import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Config
API_URL = "https://cms.rebogroep.nl/api/collections/private_objects_rent_sale/entries"
PUBLIC_LISTING_URL = "https://www.rebogroep.nl/nl/particulier/ons-aanbod/huren"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
STATE_FILE = "last_count.txt"
USER_AGENT = "Mozilla/5.0 (compatible; ReboChecker/1.0; +https://example.org/)"

HEADERS = {"User-Agent": USER_AGENT}


def send_discord_message(message: str):
    if not WEBHOOK_URL:
        print("Geen WEBHOOK_URL gevonden; melding niet verzonden.")
        return
    try:
        payload = {"content": message}
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        print("Discord melding verzonden.")
    except Exception as e:
        print("Fout bij verzenden Discord:", e)


def try_api_limit(limit=1000):
    """Probeer CMS API met een groot limit. Return list of items or None."""
    try:
        url = f"{API_URL}?limit={limit}"
        print("Proberen API met limit:", url)
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = data.get("entries") or data.get("data") or []
        if not isinstance(items, list):
            return None
        print(f"API returned {len(items)} items")
        return items
    except Exception as e:
        print("API-aanvraag mislukt:", e)
        return None


def parse_public_page_for_links(html, base=PUBLIC_LISTING_URL):
    """Zoek alle unieke /aanbod/r... links in een HTML string."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    # 1) <a> tags pointing to aanbod items
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/aanbod/r" in href:
            full = urljoin(base, href)
            links.add(full)
    # 2) card elements with object-card class (defensief)
    for card in soup.select("a.object-card, .object-card a"):
        if card.has_attr("href"):
            full = urljoin(base, card["href"])
            links.add(full)
    # 3) search for urls in inline JSON or scripts e.g. "/nl/aanbod/r..."
    for m in re.finditer(r'(/nl/aanbod/r[^\s"\'\\<>]*)', html):
        links.add(urljoin(base, m.group(1)))
    return links


def try_public_listing_once():
    """Download the main public listing page and parse links."""
    try:
        print("Ophalen publieke pagina:", PUBLIC_LISTING_URL)
        r = requests.get(PUBLIC_LISTING_URL, headers=HEADERS, timeout=10)
        r.raise_for_status()
        html = r.text
        links = parse_public_page_for_links(html, base=PUBLIC_LISTING_URL)
        print(f"Vond {len(links)} unieke aanbod-links op de pagina.")
        return links
    except Exception as e:
        print("Fout bij ophalen publieke pagina:", e)
        return set()


def try_public_listing_paginated(max_pages=10):
    """
    Probeer pagina 1..max_pages van de publieke listing (fallback).
    Sommige sites ondersteunen ?page=x of /page/x - we proberen enkele varianten.
    """
    all_links = set()
    for p in range(1, max_pages + 1):
        # probeer parameter ?page=
        url1 = f"{PUBLIC_LISTING_URL}?page={p}"
        # en alternatief met /pagina/ (sommige sites hebben /pagina/x)
        url2 = f"{PUBLIC_LISTING_URL}/pagina/{p}"
        tried = [url1, url2]
        found_any = False
        for url in tried:
            try:
                print("Proberen pagina:", url)
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200 and r.text:
                    links = parse_public_page_for_links(r.text, base=url)
                    if links:
                        print(f"Pagina {p} ({url}) -> {len(links)} links")
                        all_links.update(links)
                        found_any = True
                else:
                    print(f"Pagina {p} ({url}) returned status {r.status_code}")
            except Exception as e:
                print("Fout bij pagina ophalen:", e)
        # stop vroeg als pagina leeg is (geen resultaten)
        if not found_any:
            # als page=1 geen data gaf, blijf proberen volgende pagina's niet zinvol
            if p == 1:
                continue
            print("Geen resultaat op pagina", p, "- stop paginatie.")
            break
    print("Totaal links via paginatie:", len(all_links))
    return all_links


def get_all_unique_offers():
    """
    Probeert in volgorde:
      1) API met hoge limit
      2) publique hoofdpagina parse
      3) paginatie fallback
    Retourneert set van unieke aanbod-URL's (of lege set).
    """
    # 1) API first
    items = try_api_limit(limit=1000)
    if items is not None and len(items) >= 200:
        # als API veel items teruggeeft (bijv. ~240) -> gebruik dit
        urls = set()
        for it in items:
            # probeer permalink/url fields
            url = it.get("permalink") or it.get("uri") or it.get("url") or it.get("permalink_url")
            if url:
                # zorg dat volledige url is
                if url.startswith("/"):
                    url = urljoin("https://rebogroep.nl", url)
            else:
                # fallback: probeer raw_data of origin id
                url = None
            if url:
                urls.add(url)
        if urls:
            print("Genoeg items via API; gebruiken van API-links.")
            return urls
        # indien items bestaan maar geen urls extractable, fallback to counting items
        print("API gaf items maar geen permalinks; terugvallen op tellen via items.")
        return set([f"item-{i}" for i in range(len(items))])

    # 2) Try public listing page
    links = try_public_listing_once()
    if len(links) >= 200:
        return links

    # 3) Paginated fallback
    links = try_public_listing_paginated(max_pages=20)
    if links:
        return links

    # 4) last resort: try the API even if small - use its count
    if items is not None:
        print("Gebruik API-telling als laatste redmiddel:", len(items))
        return set([f"item-{i}" for i in range(len(items))])

    return set()


def load_last_count():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return None


def save_last_count(count):
    with open(STATE_FILE, "w") as f:
        f.write(str(count))


def main():
    print("Start controle REBO ...")
    offers = get_all_unique_offers()
    current = len(offers)
    last = load_last_count()

    print(f"Actueel aantal (gevonden): {current}")
    print(f"Vorig aantal : {last}")

    if last is None:
        print("Nog geen historie → opslaan.")
        save_last_count(current)
        return

    if current != last:
        diff = current - last
        sign = "meer" if diff > 0 else "minder"
        message = (
            f"🔔 **REBO wijziging gedetecteerd!**\n"
            f"Er zijn nu **{current}** huurwoningen ({abs(diff)} {sign})."
        )
        print(message)
        send_discord_message(message)

    save_last_count(current)


if __name__ == "__main__":
    main()
