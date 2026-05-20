from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CoffeeShop, ShopAmenity, ShopDrink, ShopPurpose, ShopSpace
from app.repositories.shop_repository import shop_repository
from app.schemas import CoffeeShopCreate, CoffeeShopUpdate, FilterOptionsResponse
from app.utils import slugify_vietnamese


class ShopService:
    """Business logic for coffee shop operations."""

    def __init__(self):
        self.repository = shop_repository

    async def list_shops(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        district: Optional[list[str]] = None,
        purpose: Optional[list[str]] = None,
        space: Optional[list[str]] = None,
        amenity: Optional[list[str]] = None,
        status: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        page: int = 1,
        limit: int = 30,
    ) -> tuple[list[CoffeeShop], int]:
        """Get filtered shop listing."""
        return await self.repository.get_filtered(
            db,
            search=search,
            district=district,
            purpose=purpose,
            space=space,
            amenity=amenity,
            status=status,
            lat=lat,
            lon=lon,
            page=page,
            limit=limit,
        )

    async def get_shop_by_id(self, db: AsyncSession, shop_id: int) -> Optional[CoffeeShop]:
        """Get a single shop by ID."""
        return await self.repository.get_by_id(db, shop_id)

    async def get_shop_by_slug(self, db: AsyncSession, slug: str) -> Optional[CoffeeShop]:
        """Get a single shop by slug."""
        return await self.repository.get_by_slug(db, slug)

    async def get_map_shops(self, db: AsyncSession) -> list[CoffeeShop]:
        """Get lightweight shop records for map display."""
        return await self.repository.get_map_shops(db)

    async def get_top_rated_shops(
        self, db: AsyncSession, limit: int = 10
    ) -> list[CoffeeShop]:
        """Get the highest-rated shops for the Top 10 page."""
        return await self.repository.get_top_rated(db, limit=limit)

    async def create_shop(self, db: AsyncSession, shop_data: CoffeeShopCreate) -> CoffeeShop:
        """Create a new coffee shop with unique slug and relationships."""
        slug = slugify_vietnamese(shop_data.name)

        # Ensure unique slug
        existing = await self.repository.get_by_slug(db, slug)
        if existing:
            counter = 1
            while True:
                new_slug = f"{slug}-{counter}"
                if not await self.repository.get_by_slug(db, new_slug):
                    slug = new_slug
                    break
                counter += 1

        shop = CoffeeShop(
            name=shop_data.name,
            slug=slug,
            address=shop_data.address,
            district=shop_data.district,
            phone=shop_data.phone,
            image_url=shop_data.image_url,
            description=shop_data.description,
            opening_hours=shop_data.opening_hours,
            price_range=shop_data.price_range,
            status=shop_data.status,
            latitude=shop_data.latitude,
            longitude=shop_data.longitude,
        )

        # Add relationships
        for p in shop_data.purposes:
            shop.purposes.append(ShopPurpose(purpose=p))
        for s in shop_data.spaces:
            shop.spaces.append(ShopSpace(space_type=s))
        for a in shop_data.amenities:
            shop.amenities.append(ShopAmenity(amenity=a))
        for d in shop_data.drinks:
            shop.drinks.append(
                ShopDrink(
                    name=d.name,
                    price=d.price,
                    category=d.category,
                    is_signature=d.is_signature,
                    is_trending=d.is_trending,
                )
            )

        db.add(shop)
        await db.commit()
        await db.refresh(shop)

        # Reload with relationships
        return await self.repository.get_by_id(db, shop.id)

    async def update_shop(
        self, db: AsyncSession, shop_id: int, shop_data: CoffeeShopUpdate
    ) -> Optional[CoffeeShop]:
        """Update an existing coffee shop."""
        shop = await self.repository.get_by_id(db, shop_id)
        if not shop:
            return None

        update_data = shop_data.model_dump(exclude_unset=True)

        # Handle relationships separately
        purposes = update_data.pop("purposes", None)
        spaces = update_data.pop("spaces", None)
        amenities = update_data.pop("amenities", None)
        drinks = update_data.pop("drinks", None)

        # Update simple fields
        for key, value in update_data.items():
            setattr(shop, key, value)

        # Regenerate slug if name changed
        if "name" in update_data:
            slug = slugify_vietnamese(update_data["name"])
            existing = await self.repository.get_by_slug(db, slug)
            if existing and existing.id != shop_id:
                counter = 1
                while True:
                    new_slug = f"{slug}-{counter}"
                    existing = await self.repository.get_by_slug(db, new_slug)
                    if not existing or existing.id == shop_id:
                        slug = new_slug
                        break
                    counter += 1
            shop.slug = slug

        # Update relationships
        if purposes is not None:
            for p in shop.purposes:
                await db.delete(p)
            shop.purposes = [ShopPurpose(purpose=p) for p in purposes]

        if spaces is not None:
            for s in shop.spaces:
                await db.delete(s)
            shop.spaces = [ShopSpace(space_type=s) for s in spaces]

        if amenities is not None:
            for a in shop.amenities:
                await db.delete(a)
            shop.amenities = [ShopAmenity(amenity=a) for a in amenities]

        if drinks is not None:
            for d in shop.drinks:
                await db.delete(d)
            shop.drinks = [
                ShopDrink(
                    name=d["name"],
                    price=d.get("price"),
                    category=d.get("category", "drink"),
                    is_signature=d.get("is_signature", False),
                    is_trending=d.get("is_trending", False),
                )
                for d in drinks
            ]

        await db.commit()
        return await self.repository.get_by_id(db, shop_id)

    async def delete_shop(self, db: AsyncSession, shop_id: int) -> bool:
        """Delete a coffee shop."""
        shop = await self.repository.get_by_id(db, shop_id)
        if not shop:
            return False
        await db.delete(shop)
        await db.commit()
        return True

    async def get_filter_options(self, db: AsyncSession) -> FilterOptionsResponse:
        """Get all available filter options."""
        return FilterOptionsResponse(
            districts=await self.repository.get_distinct_districts(db),
            purposes=await self.repository.get_distinct_purposes(db),
            spaces=await self.repository.get_distinct_spaces(db),
            amenities=await self.repository.get_distinct_amenities(db),
        )


shop_service = ShopService()
