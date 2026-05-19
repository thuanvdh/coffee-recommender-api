import asyncio
from sqlalchemy import select, func
from app.database import async_session
from app.models import CoffeeShop, ShopImage

async def main():
    async with async_session() as session:
        # Total shops
        total_shops = await session.execute(select(func.count(CoffeeShop.id)))
        # Shops with Cloudinary cover images
        cloudinary_shops = await session.execute(
            select(func.count(CoffeeShop.id)).where(CoffeeShop.image_url.like('%cloudinary.com%'))
        )
        # Shops with non-Cloudinary cover images (that are not null)
        other_shops = await session.execute(
            select(func.count(CoffeeShop.id))
            .where(CoffeeShop.image_url.isnot(None))
            .where(~CoffeeShop.image_url.like('%cloudinary.com%'))
        )
        # Total gallery images on Cloudinary
        cloudinary_images = await session.execute(
            select(func.count(ShopImage.id)).where(ShopImage.url.like('%cloudinary.com%'))
        )
        # Total gallery images NOT on Cloudinary
        other_images = await session.execute(
            select(func.count(ShopImage.id)).where(~ShopImage.url.like('%cloudinary.com%'))
        )
        
        # Select details of the mismatch shops
        result = await session.execute(
            select(CoffeeShop.name, CoffeeShop.slug, CoffeeShop.image_url)
            .where(CoffeeShop.image_url.isnot(None))
            .where(~CoffeeShop.image_url.like('%cloudinary.com%'))
        )
        print("Shops without Cloudinary cover:")
        rows = result.all()
        for row in rows:
            print(f"- {row[0]} ({row[1]}): {row[2]}")
        print(f"Total remaining shops without Cloudinary: {len(rows)}")
        
        print(f"Total shops in DB: {total_shops.scalar()}")
        print(f"Shops with Cloudinary cover: {cloudinary_shops.scalar()}")
        print(f"Shops with non-Cloudinary cover: {other_shops.scalar()}")
        print(f"Gallery images on Cloudinary: {cloudinary_images.scalar()}")
        print(f"Gallery images not on Cloudinary: {other_images.scalar()}")





if __name__ == "__main__":
    asyncio.run(main())

