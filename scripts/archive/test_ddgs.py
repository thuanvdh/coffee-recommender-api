from duckduckgo_search import DDGS
import re

def test_ddg(name):
    query = f"{name} Da Nang site:google.com/maps OR site:maps.app.goo.gl"
    print(f"Searching: {query}")
    try:
        results = DDGS().text(query, max_results=3)
        for r in results:
            url = r['href']
            print("Found URL:", url)
            if 'maps' in url or 'goo.gl' in url:
                print("Best match:", url)
                return url
    except Exception as e:
        print("Error:", e)
    return None

test_ddg("No Nee Eatery & Cafe")
test_ddg("Solis Coffee Brunch & Beer")
