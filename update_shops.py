import json
import random

with open("crawled_shops.json", "r", encoding="utf-8") as f:
    shops = json.load(f)

# Expanded drink pools (category: drink)
drink_pools = [
    [
        {"name": "Cà phê sữa đá", "price": "29,000đ", "category": "drink"}, 
        {"name": "Bạc xỉu", "price": "35,000đ", "category": "drink"}, 
        {"name": "Trà đào cam sả", "price": "45,000đ", "category": "drink"}, 
        {"name": "Cà phê muối", "price": "35,000đ", "category": "drink"}
    ],
    [
        {"name": "Cold Brew", "price": "55,000đ", "category": "drink"}, 
        {"name": "Latte", "price": "45,000đ", "category": "drink"}, 
        {"name": "Cappuccino", "price": "45,000đ", "category": "drink"}
    ],
    [
        {"name": "Sinh tố Dâu", "price": "40,000đ", "category": "drink"}, 
        {"name": "Americano", "price": "35,000đ", "category": "drink"}, 
        {"name": "Trà ổi hồng", "price": "45,000đ", "category": "drink"}, 
        {"name": "Nước ép cam", "price": "40,000đ", "category": "drink"}
    ]
]

# Pastry pool (category: pastry)
pastry_pool = [
    {"name": "Bánh Tiramisu", "price": "45,000đ", "category": "pastry"},
    {"name": "Bánh Mousse Đào", "price": "42,000đ", "category": "pastry"},
    {"name": "Bánh Phô mai nướng", "price": "48,000đ", "category": "pastry"},
    {"name": "Croissant Bơ Pháp", "price": "35,000đ", "category": "pastry"},
    {"name": "Bánh Red Velvet", "price": "50,000đ", "category": "pastry"},
    {"name": "Bánh Brownie", "price": "38,000đ", "category": "pastry"}
]

descriptions = [
    "Một không gian ấm cúng mang lại cảm giác thư giãn giữa lòng thành phố náo nhiệt. Quán {name} là điểm đến lý tưởng cho những buổi tụ tập bạn bè hoặc làm việc.",
    "Với thiết kế hiện đại và không gian thoáng đãng, {name} mang đến trải nghiệm thưởng thức cà phê tuyệt vời nhất cho khách hàng. Menu đa dạng với các món nước signature.",
    "Nếu bạn đang tìm một góc yên tĩnh để đọc sách hay tập trung làm việc, {name} chính là sự lựa chọn hoàn hảo. Không gian xanh mát và yên bình.",
    "Quán cà phê mang phong cách vintage độc đáo. {name} không chỉ có đồ uống ngon mà còn là nơi check-in lý tưởng cho các bạn trẻ."
]

for i, shop in enumerate(shops):
    # Select a random pool of drinks
    base_menu = random.choice(drink_pools).copy()
    
    # Add random pastries (1-2 per shop)
    base_menu.extend(random.sample(pastry_pool, random.randint(1, 2)))
    
    # Enrich with flags
    # We want at least one signature and one trending in the whole menu
    sig_idx = random.randint(0, len(base_menu) - 1)
    trend_idx = random.randint(0, len(base_menu) - 1)
    
    enriched_menu = []
    for j, item in enumerate(base_menu):
        item_copy = item.copy()
        item_copy["is_signature"] = (j == sig_idx)
        item_copy["is_trending"] = (j == trend_idx)
        enriched_menu.append(item_copy)
        
    shop["drinks"] = enriched_menu
    shop["description"] = random.choice(descriptions).format(name=shop["name"])

with open("crawled_shops.json", "w", encoding="utf-8") as f:
    json.dump(shops, f, ensure_ascii=False, indent=2)

print(f"Updated all {len(shops)} shops in crawled_shops.json with categorized menu!")
