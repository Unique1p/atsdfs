import os
import requests
from bs4 import BeautifulSoup

URL = "https://www.rebogroep.nl/nl/particulier/ons-aanbod/huren"

response = requests.get(URL, timeout=10)
print("=== HTML BEGIN ===")
print(response.text[:2000])            # eerste 2000 tekens
print("=== HTML EINDE ===")

soup = BeautifulSoup(response.text, "html.parser")

print("\n=== ALLE <h2> ELEMENTEN ===")
for h2 in soup.find_all("h2"):
    print("-", repr(h2.get_text(strip=True)))
