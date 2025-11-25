import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
URL = "https://www.rebogroep.nl/nl/particulier/ons-aanbod/huren"

def check_results():
    response = requests.get(URL, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Zoek het aantal woningen — dit moet jij misschien aanpassen
    count_elem = soup.find("span", {"class": "results-count"})
    if not count_elem:
        print("❌ Kon de count niet vinden op de pagina.")
        return

    count = int(count_elem.text.strip())

    # Verstuur melding naar Discord
    data = {
        "content": f"🏠 Rebo woningen beschikbaar: **{count}**"
    }

    r = requests.post(WEBHOOK_URL, json=data)
    print("Discord webhook verstuurd:", r.status_code)

if __name__ == "__main__":
    check_results()
