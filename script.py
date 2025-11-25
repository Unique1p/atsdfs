import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
URL = "https://www.rebogroep.nl/nl/particulier/ons-aanbod/huren"

def check_results():
    response = requests.get(URL, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Zoek het <h2> element dat eindigt op "resultaten"
    h2_elements = soup.find_all("h2")

    count = None
    for h2 in h2_elements:
        text = h2.get_text(strip=True)
        if text.endswith("resultaten"):
            # Tekst is bijvoorbeeld "240 resultaten"
            count = int(text.split()[0])
            break

    if count is None:
        print("❌ Kon de count niet vinden op de pagina.")
        return

    # Verstuur melding naar Discord
    data = {
        "content": f"🏠 Rebo woningen beschikbaar: **{count}**"
    }
    r = requests.post(WEBHOOK_URL, json=data)
    print("Discord webhook verstuurd:", r.status_code)

if __name__ == "__main__":
    check_results()
