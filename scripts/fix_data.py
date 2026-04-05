import asyncio
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import CoffeeShop, ShopImage, Base

DATABASE_URL = "postgresql+asyncpg://danang_coffee:danang_coffee_2024@coffee-db:5432/danang_coffee"

DISTRICT_COORDS = {
    "Hải Châu": (16.0471, 108.2198),
    "Thanh Khê": (16.0645, 108.1925),
    "Sơn Trà": (16.0716, 108.2323),
    "Ngũ Hành Sơn": (16.0305, 108.2505),
    "Liên Chiểu": (16.0601, 108.1481),
    "Cẩm Lệ": (16.0216, 108.1965)
}

MOCK_IMAGES = [
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800&q=80",
    "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80",
    "https://images.unsplash.com/photo-1507133750040-4a8f57021571?w=800&q=80",
    "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=800&q=80",
    "https://images.unsplash.com/photo-1506619216599-9d16d0903dfd?w=800&q=80",
    "https://images.unsplash.com/photo-1497933321188-941f9ad36b17?w=800&q=80",
    "https://images.unsplash.com/photo-1541167760496-162955ed8a9f?w=800&q=80",
    "https://images.unsplash.com/photo-1498804103079-a6351b050096?w=800&q=80"
]

async def fix_data():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Get all shops
        result = await session.execute(select(CoffeeShop))
        shops = result.scalars().all()
        print(f"Fixing data for {len(shops)} shops...")

        for shop in shops:
            # 2. Assign coordinates
            base_lat, base_lon = DISTRICT_COORDS.get(shop.district, (16.0544, 108.2022))
            shop.latitude = base_lat + (random.random() - 0.5) * 0.02
            shop.longitude = base_lon + (random.random() - 0.5) * 0.02

            # 3. Add gallery images (if none exist)
            # Check existing images
            img_check = await session.execute(select(ShopImage).where(ShopImage.shop_id == shop.id))
            if not img_check.scalars().first():
                # Add 3 random mock images
                selected = random.sample(MOCK_IMAGES, 3)
                for url in selected:
                    session.add(ShopImage(shop_id=shop.id, url=url, alt_text=f"Không gian tại {shop.name}"))
        
        await session.commit()
    
    print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_data())
