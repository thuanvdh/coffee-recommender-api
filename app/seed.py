"""
Seed script to populate initial coffee shop data.
Run with: python -m app.seed
"""

import asyncio
import random

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base, CoffeeShop, ShopAmenity, ShopPurpose, ShopSpace, ShopStatus, ShopDrink
from app.crud import _slugify

import json
import os

# ========== DATA SOURCE ==========
SHOPS_DATA = []
CRAWLED_FILE = "crawled_shops.json"

if os.path.exists(CRAWLED_FILE):
    try:
        with open(CRAWLED_FILE, "r", encoding="utf-8") as f:
            SHOPS_DATA = json.load(f)
        print(f"📄 Đã nạp {len(SHOPS_DATA)} quán từ {CRAWLED_FILE}")
    except Exception as e:
        print(f"⚠️ Lỗi khi đọc {CRAWLED_FILE}: {e}")

# Fallback to hardcoded sample if JSON is empty or missing
if not SHOPS_DATA:
    SHOPS_DATA = [
        {
            "name": "Trình cà phê – VTV8",
            "address": "256 Bạch Đằng, P. Hải Châu, TP. Đà Nẵng",
            "district": "Hải Châu",
            "purposes": ["Đọc sách - học bài", "Ngồi làm việc", "Tụ tập bạn bè", "Xuyên đêm 24/7"],
            "spaces": ["Ngoài trời", "Trong nhà", "Vỉa hè", "View sông, biển"],
            "amenities": ["Bánh ngọt", "Chỗ đậu xe", "Được hút thuốc", "Wifi miễn phí"],
            "image_url": "https://danang.coffee/wp-content/uploads/2024/03/trinh-vtv8-thumbnail.jpg",
            "status": ShopStatus.NEW.value
        }
    ]

ALL_PURPOSES = ["Đọc sách - học bài", "Không gian riêng tư", "Ngồi làm việc", "Tụ tập bạn bè", "Yên tĩnh", "Take away", "Cafe Kid", "Xuyên đêm 24/7", "Tổ chức Workshop", "Đêm nhạc Acoustic"]
ALL_SPACES = ["Ngoài trời", "Trong nhà", "Ban công", "Sân thượng", "Không gian nhỏ", "Vỉa hè", "Sân vườn", "View hoàng hôn", "View sông, biển", "View ngắm máy bay"]
ALL_AMENITIES = ["Chỗ đậu xe", "Máy lạnh", "Bánh ngọt", "Được hút thuốc", "Phục vụ đồ ăn", "Wifi miễn phí", "Ổ cắm điện", "Phòng riêng", "Nhạc sống", "Pet-friendly"]

async def seed_data():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        print("🧹 Đang dọn dẹp dữ liệu cũ...")
        await session.execute(delete(ShopDrink))
        await session.execute(delete(ShopAmenity))
        await session.execute(delete(ShopPurpose))
        await session.execute(delete(ShopSpace))
        await session.execute(delete(CoffeeShop))
        await session.commit()

        print(f"🌱 Đang seed dữ liệu quán cà phê mới ({len(SHOPS_DATA)} quán)...")
        random.seed(42)
        seen_slugs = set()

        for shop_data in SHOPS_DATA:
            base_slug = _slugify(shop_data["name"])
            slug = base_slug
            counter = 1
            while slug in seen_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            seen_slugs.add(slug)
            
            shop = CoffeeShop(
                name=shop_data["name"],
                slug=slug,
                address=shop_data.get("address"),
                district=shop_data.get("district"),
                image_url=shop_data.get("image_url", "/images/shop-1.jpg"),
                status=shop_data.get("status", ShopStatus.OPEN.value),
                latitude=shop_data.get("latitude"),
                longitude=shop_data.get("longitude"),
                price_range=random.choice(["20k - 50k", "30k - 60k", "40k - 80k"]),
                opening_hours=random.choice(["07:00 - 22:00", "06:30 - 23:00", "24/7"]),
                description=shop_data.get("description", "")
            )
            session.add(shop)
            await session.flush()

            # Assign purposes (either from data or random)
            purposes = shop_data.get("purposes", random.sample(ALL_PURPOSES, random.randint(2, 4)))
            for p in purposes:
                session.add(ShopPurpose(shop_id=shop.id, purpose=p))

            # Assign spaces
            spaces = shop_data.get("spaces", random.sample(ALL_SPACES, random.randint(1, 2)))
            for s in spaces:
                session.add(ShopSpace(shop_id=shop.id, space_type=s))

            # Assign amenities
            amenities = shop_data.get("amenities", random.sample(ALL_AMENITIES, random.randint(2, 4)))
            for a in amenities:
                session.add(ShopAmenity(shop_id=shop.id, amenity=a))

            # Assign drinks
            drinks = shop_data.get("drinks", [])
            for d in drinks:
                session.add(ShopDrink(
                    shop_id=shop.id, 
                    name=d["name"], 
                    price=d.get("price"),
                    category=d.get("category", "drink"),
                    is_signature=d.get("is_signature", False),
                    is_trending=d.get("is_trending", False)
                ))

        await session.commit()
        print(f"✅ Đã seed {len(SHOPS_DATA)} quán cà phê thành công!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())
