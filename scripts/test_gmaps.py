import httpx
from urllib.parse import quote
import re

def parse_gmaps(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    url = f"https://www.google.com/maps/search/{quote(query)}"
    print(f"Fetching: {url}")
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        r = client.get(url, timeout=30.0)
        
        # In the HTML, there are often strings containing lat/lng for specific places.
        # Let's search for the pattern "[16.xxxxx, 108.yyyyy]" or similar inside the APP_INITIALIZATION_STATE
        
        # Extract APP_INITIALIZATION_STATE
        match = re.search(r'window\.APP_INITIALIZATION_STATE=\[\[(.*?)\]\]\];', r.text)
        if match:
            state_data = match.group(1)
            # Find coordinates that match Da Nang
            # Usually they appear as: null,null,16.0xxxx,108.yyyyy
            coords = re.findall(r'null,null,(15\.\d+|16\.\d+),(107\.\d+|108\.\d+)', state_data)
            if coords:
                print(f"Found coords in state: {coords[0][0]}, {coords[0][1]}")
                return
                
        # Sometimes it's in a different spot
        coords2 = re.findall(r'\[(15\.\d+|16\.\d+),(107\.\d+|108\.\d+)\]', r.text)
        if coords2:
            print(f"Found coords loosely: {coords2[0][0]}, {coords2[0][1]}")
            return
            
        print("Not found")

parse_gmaps("Cộng Cà Phê Đà Nẵng")
parse_gmaps("The Local Beans Đà Nẵng")
