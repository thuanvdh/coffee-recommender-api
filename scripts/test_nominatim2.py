import httpx
from urllib.parse import quote
import asyncio

async def test_nominatim(name):
    query = quote(f"{name}, Đà Nẵng, Vietnam")
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
    headers = {
        "User-Agent": "CoffeeRecommender/1.0 (test@example.com)",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        r = await client.get(url, timeout=30.0)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"Found: {data[0]['lat']}, {data[0]['lon']}")
            else:
                print("No results")
        else:
            print("Failed:", r.text[:200])

asyncio.run(test_nominatim("Cộng Cà Phê"))
asyncio.run(test_nominatim("The Local Beans"))
