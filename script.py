import os
import requests

API_URL = "https://cms.rebogroep.nl/api/collections/private_objects_rent_sale/entries"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
STATE_FILE = "last_count.txt"

def send_discord_message(message: str):
    if not WEBHOOK_URL:
        print("Geen WEBHOOK_URL gevonden")
        return
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload, timeout=10)


def get_current_count():
    print("Ophalen van REBO API ...")
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    return len(data.get("entries", data.get("data", [])))


def load_last_count():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return None


def save_last_count(count):
    with open(STATE_FILE, "w") as f:
        f.write(str(count))


def main():
    current = get_current_count()
    last = load_last_count()

    print(f"Actueel aantal: {current}")
    print(f"Vorig aantal : {last}")

    if last is None:
        print("Nog geen historie → opslaan.")
        save_last_count(current)
        return

    if current != last:
        diff = current - last
        sign = "meer" if diff > 0 else "minder"
        message = f"🔔 REBO wijziging gedetecteerd!\nEr zijn nu **{current}** huurwoningen ({abs(diff)} {sign})."
        print(message)
        send_discord_message(message)

    save_last_count(current)


if __name__ == "__main__":
    main()
