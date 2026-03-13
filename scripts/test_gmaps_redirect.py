import httpx
from urllib.parse import quote

def test_gmaps_lucky(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.google.com/maps?q={quote(query)}"
    print(f"Fetching: {url}")
    with httpx.Client(headers=headers, follow_redirects=False) as client:
        r = client.get(url, timeout=30.0)
        print(f"Status: {r.status_code}")
        if r.status_code in [301, 302, 307, 308]:
            print(f"Redirects to: {r.headers.get('Location')}")
        else:
            print("No redirect.")

test_gmaps_lucky("The Local Beans Đà Nẵng")
test_gmaps_lucky("Cộng Cà Phê Đà Nẵng")
