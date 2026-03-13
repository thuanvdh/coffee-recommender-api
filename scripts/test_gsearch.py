from googlesearch import search

def test_gsearch(name):
    query = f"{name} Đà Nẵng site:google.com/maps OR site:maps.app.goo.gl"
    print(f"Searching: {query}")
    try:
        results = search(query, num_results=1, sleep_interval=2)
        for url in results:
            print("Found URL:", url)
            return url
    except Exception as e:
        print("Error:", e)
    return None

test_gsearch("No Nee Eatery & Cafe")
test_gsearch("Solis Coffee Brunch & Beer")
