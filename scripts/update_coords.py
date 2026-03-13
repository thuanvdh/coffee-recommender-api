import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import quote

DATA_FILE = "crawled_shops.json"
# Simplified User-Agent and synchronous helper for map links
MAP_HEADERS = {"User-Agent": "Mozilla/5.0"}
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search?format=json&q="

def get_coords_sync(map_url):
    try:
        # Use synchronous httpx.get as it proved to work better with redirects
        with httpx.Client(headers=MAP_HEADERS, follow_redirects=False) as client:
            r = client.get(map_url, timeout=30.0)
            if r.status_code in [301, 302, 307, 308]:
                final_url = r.headers.get("location", "")
            else:
                final_url = str(r.url)
            
            print(f"    🔗 Resolved URL: {final_url}", flush=True)
            
            # Patterns
            patterns = [
                r'search/(-?\d+\.\d+),(-?\d+\.\d+)',
                r'@(-?\d+\.\d+),(-?\d+\.\d+)',
                r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)'
            ]
            for p in patterns:
                match = re.search(p, final_url)
                if match:
                    return float(match.group(1)), float(match.group(2))
        return None, None
    except Exception as e:
        print(f"    ❌ Sync Error {map_url}: {e}", flush=True)
        return None, None

async def geocode_address(client, address):
    try:
        # Ensure focus on Da Nang
        query = quote(f"{address}, Đà Nẵng, Vietnam")
        url = f"{NOMINATIM_URL}{query}"
        response = await client.get(url, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except Exception as e:
        print(f"    ❌ Geocoding Error: {e}", flush=True)
        return None, None

async def process_shop(client, shop):
    if shop.get('latitude') and shop.get('longitude'):
        return False
    
    source_url = shop.get('source_url')
    name = shop.get('name')
    address = shop.get('address')
    
    print(f"🔍 Processing: {name}", flush=True)
    
    # 1. Try Map Link if source_url exists
    if source_url:
        try:
            response = await client.get(source_url, timeout=30.0)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                map_el = soup.select_one('a.jet-listing-dynamic-link__link[href*="maps.app.goo.gl"]')
                if not map_el:
                    map_el = soup.select_one('a[href*="google.com/maps"]')
                    
                if map_el:
                    map_url = map_el['href']
                    print(f"  📍 Map Link found: {map_url}", flush=True)
                    lat, lng = get_coords_sync(map_url)
                    if lat and lng:
                        shop['latitude'] = lat
                        shop['longitude'] = lng
                        print(f"  ✅ Coords (Map): {lat}, {lng}", flush=True)
                        return True
        except Exception as e:
            print(f"  ❌ Source Page Error: {e}", flush=True)

    # 2. Fallback to Address Geocoding
    if address:
        print(f"  🏠 Geocoding address: {address}", flush=True)
        lat, lng = await geocode_address(client, address)
        if lat and lng:
            shop['latitude'] = lat
            shop['longitude'] = lng
            print(f"  ✅ Coords (Geocode): {lat}, {lng}", flush=True)
            return True
            
    print("  ❌ No coordinates found.", flush=True)
    return False

async def main():
    if not os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        shops = json.load(f)

    print(f"🚀 Updating coordinates for {len(shops)} shops...", flush=True)
    
    async with httpx.AsyncClient(headers={"User-Agent": "CoffeeExplorer (thuanho@example.com)"}) as client:
        updated_count = 0
        for i, shop in enumerate(shops):
            updated = await process_shop(client, shop)
            if updated:
                updated_count += 1
                if updated_count % 5 == 0:
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(shops, f, ensure_ascii=False, indent=2)
                    print(f"💾 Checkpoint: {updated_count} shops", flush=True)
                
                # Sleep to respect rate limits (especially Nominatim)
                await asyncio.sleep(1.5)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(shops, f, ensure_ascii=False, indent=2)
        
    print(f"🏁 Finished! Updated {updated_count} shops.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
