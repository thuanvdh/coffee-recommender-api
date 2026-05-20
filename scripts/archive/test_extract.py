import httpx
from urllib.parse import quote
import re
import json

def test_extract_state(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    url = f"https://www.google.com/maps/search/{quote(query)}"
    print(f"Fetching: {url}")
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        r = client.get(url, timeout=30.0)
        
        match = re.search(r'window\.APP_INITIALIZATION_STATE=\[\[\[(.*?)\]\]\]', r.text)
        if match:
            with open("state.json", "w") as f:
                f.write("[[[" + match.group(1) + "]]]")
            print("Wrote state.json")
        else:
            print("Not found")

test_extract_state("The Local Beans Đà Nẵng")
