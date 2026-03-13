from ddgs import DDGS

def test_ddg_maps(shop_name):
    query = f"{shop_name} Đà Nẵng"
    print(f"Searching: {query}")
    try:
        results = DDGS().maps(query, max_results=1)
        # It yields a generator
        for r in results:
            print("Found result:", r['title'])
            if 'latitude' in r and 'longitude' in r:
                print(f"Coords: {r['latitude']}, {r['longitude']}")
                return r['latitude'], r['longitude']
            elif 'coordinates' in r:
                print(f"Coords: {r['coordinates']['latitude']}, {r['coordinates']['longitude']}")
                return r['coordinates']['latitude'], r['coordinates']['longitude']
            else:
                print("No coordinates in result:", r.keys())
    except Exception as e:
        print("Error:", e)
    return None, None

test_ddg_maps("The Local Beans")
test_ddg_maps("Thanh Thuy Coffee")
