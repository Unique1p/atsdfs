import os
import requests

API_URL = "https://cms.rebogroep.nl/api/collections/private_objects_rent_sale/entries"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
STATE_FILE = "last_count.txt"


def send_discord_message(message: str):
    """Stuur een bericht naar Discord via webhook."""
    if not WEBHOOK_URL:
        print("Geen WEBHOOK_URL gevonden")
        return
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload, timeout=10)


def get_all_entries():
    """Haalt ALLE REBO objecten op via paginatie."""
    print("Ophalen van REBO API (met paginatie)...")

    all_items = []
    offset = 0
    limit = 100  # veilig en snel

    while True:
        url = f"{API_URL}?limit={limit}&offset={offset}"
        print(f"- Fetch: offset={offset}")

        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        # De API gebruikt soms 'entries' en soms 'data'
        items = data.get("entries") or data.get("data") or []

        if not items:
            break

        all_items.extend(items)
        offset += limit

    print(f"Totaal opgehaald: {len(all_items)} items")
    return all_items


def get_current_count():
    """Tel het aantal beschikbare woningen."""
    return len(get_all_entries())


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
    current = get_current_count()
    last = load_last_count()

    print(f"\nActueel aantal: {current}")
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
            f"Er zijn nu **{current}** huurwoningen "
            f"({abs(diff)} {sign})."
        )
        print(message)
        send_discord_message(message)

    save_last_count(current)


if __name__ == "__main__":
    main()
