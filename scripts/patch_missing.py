import json

DATA_FILE = "crawled_shops.json"

manual_coords = {
    "No Nee Eatery & Cafe": {"lat": 16.0694, "lon": 108.2415, "address": "171 Hồ Nghinh, Đà Nẵng"},
    "Solis Coffee Brunch & Beer": {"lat": 16.0503, "lon": 108.2465, "address": "36 An Thượng 30, Đà Nẵng"},
    "byC. café and brunch": {"lat": 16.0822, "lon": 108.2195, "address": "07 Nguyễn Du, Đà Nẵng"},
    "Nhật là trà": {"lat": 16.0754, "lon": 108.2163, "address": "K19/10 Đinh Tiên Hoàng, Đà Nẵng"},
    "guwol.kaffe": {"lat": 16.0665, "lon": 108.1901, "address": "110 Phạm Nhữ Tăng, Đà Nẵng"},
    "Brewing Hood": {"lat": 16.0521, "lon": 108.2468, "address": "04 An Thượng 40, Đà Nẵng"},
    "Blume Kaffee": {"lat": 16.0461, "lon": 108.2045, "address": "53/3 Hoàng Thúc Trâm, Đà Nẵng"}
}

with open(DATA_FILE, "r", encoding="utf-8") as f:
    shops = json.load(f)

patched = 0
for shop in shops:
    name = shop.get("name")
    if not shop.get("latitude") and name in manual_coords:
        print(f"Patching {name}...")
        shop["latitude"] = manual_coords[name]["lat"]
        shop["longitude"] = manual_coords[name]["lon"]
        shop["address"] = manual_coords[name]["address"]
        patched += 1

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(shops, f, ensure_ascii=False, indent=2)

print(f"Patched {patched} shops.")
