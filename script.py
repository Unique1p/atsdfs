import os
import requests

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
STATE_FILE = "last_count.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"


def send_discord_message(message: str):
    if not WEBHOOK_URL:
        print("Geen WEBHOOK_URL gevonden")
        return
    requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)


def get_rebo_algolia_count():
    url = (
        "https://240m1w8agr-dsn.algolia.net/1/indexes/"
        "private_objects_rent_sale_nl_status_asc/query"
        "?x-algolia-agent=Algolia%20for%20JavaScript%20(4.24.0)%3B%20Browser"
        "&x-algolia-api-key=055822c5312edb8cf91a483936751fac"
        "&x-algolia-application-id=240M1W8AGR"
    )

    # EXACHTE payload van rebogroep.nl
    payload = {
        "query": "",
        "facetFilters": '["type_facet:rent||rent"]',
        "facets": '["*"]',
        "hitsPerPage": "21",
        "page": "0",
        "sortFacetValuesBy": "alpha",
        "maxValuesPerFacet": "99999999"
    }

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    print("Ophalen Algolia data...")
    r = requests.post(url, data=payload, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    return data.get("nbHits", 0)


def load_last_count():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        return int(open(STATE_FILE).read().strip())
    except:
        return None


def save_last_count(count):
    with open(STATE_FILE, "w") as f:
        f.write(str(count))


def main():
    print("Start controle REBO ...")

    current = get_rebo_algolia_count()
    last = load_last_count()

    print(f"Actueel aantal: {current}")
    print(f"Vorig aantal : {last}")

    if last is None:
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
