
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Tamil Nadu Government official sources only
SEED_URLS = [
    "https://tnrd.tn.gov.in/rdweb_newsite/project/reports/Public/all_schemes.php",
    "https://www.tnagrisnet.tn.gov.in/home/schemes/",
    "https://bcmbcmw.tn.gov.in/welfschemes.htm",
    "https://www.cra.tn.gov.in/about_schemes.php",
    "https://scd.tn.gov.in/specialedu.php",
    "https://tnesevai.tn.gov.in/Pages/EsevaiServiceListInstitution.aspx",
]

KEYWORDS = [
    "scheme", "schemes", "thittam", "welfare",
    "scholarship", "pension", "assistance",
    "subsidy", "eligibility", "திட்டம்", "திட்டங்கள்"
]

session = requests.Session()
session.headers.update({
    "User-Agent": "TN-Scheme-AI educational project"
})

records = []
seen = set()

def collect_page(url):
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()

        if "text/html" not in response.headers.get("Content-Type", ""):
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = soup.title.get_text(" ", strip=True) if soup.title else url
        text = soup.get_text(" ", strip=True)

        if len(text) > 250:
            records.append({
                "state": "Tamil Nadu",
                "title": title,
                "source": url,
                "content": text
            })
            print("Collected:", title[:70])

        links = []

        for a in soup.find_all("a", href=True):
            label = a.get_text(" ", strip=True)
            target = urljoin(url, a["href"]).split("#")[0]
            parsed = urlparse(target)

            if parsed.scheme not in ("http", "https"):
                continue

            if parsed.netloc != urlparse(url).netloc:
                continue

            if any(word in (label + " " + target).lower()
                   for word in KEYWORDS):
                links.append(target)

        return links

    except Exception as exc:
        print("Skipped:", url, "-", exc)
        return []

queue = list(SEED_URLS)
MAX_PAGES = 40

while queue and len(seen) < MAX_PAGES:
    url = queue.pop(0)

    if url in seen:
        continue

    seen.add(url)
    new_links = collect_page(url)

    for link in new_links:
        if link not in seen and link not in queue:
            queue.append(link)

    time.sleep(0.5)

with open("collected_schemes.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print("\nCollection finished!")
print("Pages collected:", len(records))
print("Saved: collected_schemes.json")
