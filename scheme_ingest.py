
import requests
from bs4 import BeautifulSoup
import json

URL = "https://tnrd.tn.gov.in/rdweb_newsite/project/reports/Public/all_schemes.php"

response = requests.get(
    URL,
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0"}
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

for tag in soup(["script", "style", "nav", "footer"]):
    tag.decompose()

text = soup.get_text(separator="\n", strip=True)

data = {
    "state": "Tamil Nadu",
    "department": "Rural Development",
    "source": URL,
    "content": text
}

with open("scheme_data.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("Saved scheme data to scheme_data.json")
print("Extracted characters:", len(text))
