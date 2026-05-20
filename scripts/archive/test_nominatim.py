import httpx
from urllib.parse import quote
import asyncio

async def test_nominatim(name, address=None):
    # Try name first
    query = quote(f"{name}, Đà Nẵng, Vietnam")
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
    print(f"Fetching: {url}")
    
    headers = {"User-Agent": "CoffeeExplorerTest (thuanho@example.com)"}
    async with httpx.AsyncClient(headers=headers) as client:
        r = await client.get(url, timeout=30.0)
        data = r.json()
        if data:
            print(f"Found via name: {data[0]['lat']}, {data[0]['lon']}")
        else:
            print("Not found via name")
            if address:
                query = quote(f"{address}, Đà Nẵng, Vietnam")
                url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
                print(f"Fetching address: {url}")
                r = await client.get(url, timeout=30.0)
                data = r.json()
                if data:
                    print(f"Found via address: {data[0]['lat']}, {data[0]['lon']}")
                else:
                    print("Not found via address")

async def main():
    await test_nominatim("Cộng Cà Phê")
    await test_nominatim("The Local Beans")
    await test_nominatim("Reply 1988 Cafe")

asyncio.run(main())
