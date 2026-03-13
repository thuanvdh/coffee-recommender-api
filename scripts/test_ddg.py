import httpx
from urllib.parse import quote
from bs4 import BeautifulSoup
import re

def search_duckduckgo(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        r = client.get(url, timeout=30.0)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extract maps links
        for a in soup.find_all("a", href=True):
            href = a['href']
            # DDG wraps URLs in /url?q=...
            if 'google.com/maps' in href or 'maps.app.goo.gl' in href or 'goo.gl/maps' in href:
                actual_url = re.search(r'url\?q=(.+?)&', href)
                if actual_url:
                    from urllib.parse import unquote
                    print("Found Map URL:", unquote(actual_url.group(1)))
                    return unquote(actual_url.group(1))
        
        print("No map link found")
        return None

search_duckduckgo("No Nee Eatery & Cafe Da Nang site:google.com/maps OR site:maps.app.goo.gl")
search_duckduckgo("The Local Beans Da Nang site:google.com/maps")
