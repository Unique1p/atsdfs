import os
import requests

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
STATE_FILE = "last_count.txt"
USER_AGENT = "Mozilla/5.0 (compatible; ReboChecker/1.0; +https://example.org/)"

def send_discord_message(message: str):
    if not WEBHOOK_URL:
        print("Geen WEBHOOK_URL gevonden")
        return
    requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)


def get_rebo_algolia_count():
    ALGOLIA_APP_ID = "240M1W8AGR"
    ALGOLIA_API_KEY = "055822c5312edb8cf91a483936751fac"

    url = "https://240m1w8agr-dsn.algolia.net/1/indexes/private_objects_rent_sale_nl_status_asc/query"

    headers = {
        "User-Agent": USER_AGENT,
        "X-Algolia-Application-Id": ALGOLIA_APP_ID,
        "X-Algolia-API-Key": ALGOLIA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "params": "query=&hitsPerPage=500&page=0&facetFilters=%5B%22transactionType:rent%22%5D"
    }

    print("Ophalen Algolia data...")
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    return data.get("nbHits", 0)


def get_current_count():
    try:
        return get_rebo_algolia_count()
    except Exception as e:
        print("Algolia mislukt:", e)
        return 0


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

    current = get_current_count()
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
