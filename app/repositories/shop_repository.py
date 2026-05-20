from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CoffeeShop,
    Review,
    ShopAmenity,
    ShopPurpose,
    ShopSpace,
)
from app.repositories.base import BaseRepository
from app.schemas import CoffeeShopCreate, CoffeeShopUpdate


def _shop_eager_options():
    """Standard eager-loading options for CoffeeShop queries."""
    return [
        selectinload(CoffeeShop.purposes),
        selectinload(CoffeeShop.spaces),
        selectinload(CoffeeShop.amenities),
        selectinload(CoffeeShop.drinks),
        selectinload(CoffeeShop.images),
        selectinload(CoffeeShop.reviews),
    ]


class ShopRepository(BaseRepository[CoffeeShop, CoffeeShopCreate, CoffeeShopUpdate]):
    """Repository for CoffeeShop data access."""

    async def get_by_id(self, db: AsyncSession, shop_id: int) -> Optional[CoffeeShop]:
        """Get a single shop by ID with all relationships loaded."""
        query = (
            select(CoffeeShop)
            .options(*_shop_eager_options())
            .where(CoffeeShop.id == shop_id)
        )
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[CoffeeShop]:
        """Get a single shop by slug with all relationships loaded."""
        query = (
            select(CoffeeShop)
            .options(*_shop_eager_options())
            .where(CoffeeShop.slug == slug)
        )
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_filtered(
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
        """Get shops with filters, search, geo-distance, and pagination."""
        distance_expr = None
        if lat is not None and lon is not None:
            distance_expr = (
                6371
                * func.acos(
                    func.cos(func.radians(lat))
                    * func.cos(func.radians(CoffeeShop.latitude))
                    * func.cos(func.radians(CoffeeShop.longitude) - func.radians(lon))
                    + func.sin(func.radians(lat))
                    * func.sin(func.radians(CoffeeShop.latitude))
                )
            ).label("distance_km")
            query = select(CoffeeShop, distance_expr).options(*_shop_eager_options())
        else:
            query = select(CoffeeShop).options(*_shop_eager_options())

        count_query = select(func.count(func.distinct(CoffeeShop.id)))

        # Search filter
        if search:
            search_filter = (
                CoffeeShop.name.ilike(f"%{search}%")
                | CoffeeShop.address.ilike(f"%{search}%")
                | CoffeeShop.district.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # District filter
        if district:
            district_filter = CoffeeShop.district.in_(district)
            query = query.where(district_filter)
            count_query = count_query.where(district_filter)

        # Static status filter (not open/closed_temp which need runtime check)
        if status and status not in ("open", "closed_temp"):
            query = query.where(CoffeeShop.status == status)
            count_query = count_query.where(CoffeeShop.status == status)

        # Purpose filter
        if purpose:
            query = query.join(CoffeeShop.purposes).where(
                ShopPurpose.purpose.in_(purpose)
            )
            count_query = count_query.join(
                ShopPurpose, CoffeeShop.id == ShopPurpose.shop_id
            ).where(ShopPurpose.purpose.in_(purpose))

        # Space filter
        if space:
            query = query.join(CoffeeShop.spaces).where(
                ShopSpace.space_type.in_(space)
            )
            count_query = count_query.join(
                ShopSpace, CoffeeShop.id == ShopSpace.shop_id
            ).where(ShopSpace.space_type.in_(space))

        # Amenity filter
        if amenity:
            query = query.join(CoffeeShop.amenities).where(
                ShopAmenity.amenity.in_(amenity)
            )
            count_query = count_query.join(
                ShopAmenity, CoffeeShop.id == ShopAmenity.shop_id
            ).where(ShopAmenity.amenity.in_(amenity))

        # Dynamic status (open/closed_temp) requires runtime filtering
        if status in ("open", "closed_temp"):
            from app.utils import is_shop_open_now

            if distance_expr is not None:
                query = query.order_by(
                    distance_expr.asc().nulls_last(), CoffeeShop.created_at.desc()
                )
            else:
                query = query.order_by(CoffeeShop.created_at.desc())

            result = await db.execute(query)
            if distance_expr is not None:
                rows = result.unique().all()
                all_shops = []
                for shop, dist in rows:
                    shop.distance_km = dist
                    all_shops.append(shop)
            else:
                all_shops = list(result.unique().scalars().all())

            filtered_shops = []
            for shop in all_shops:
                is_open = is_shop_open_now(shop.opening_hours)
                if status == "open" and is_open:
                    filtered_shops.append(shop)
                elif status == "closed_temp" and not is_open:
                    filtered_shops.append(shop)

            total = len(filtered_shops)
            offset = (page - 1) * limit
            return filtered_shops[offset : offset + limit], total

        # Regular flow
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        if distance_expr is not None:
            query = query.order_by(
                distance_expr.asc().nulls_last(), CoffeeShop.created_at.desc()
            ).offset(offset).limit(limit)
        else:
            query = query.order_by(CoffeeShop.created_at.desc()).offset(offset).limit(
                limit
            )

        result = await db.execute(query)
        if distance_expr is not None:
            rows = result.unique().all()
            shops = []
            for shop, dist in rows:
                shop.distance_km = dist
                shops.append(shop)
        else:
            shops = list(result.unique().scalars().all())

        return shops, total

    async def get_map_shops(self, db: AsyncSession) -> list[CoffeeShop]:
        """Get lightweight shop records that can be displayed on a map."""
        result = await db.execute(
            select(CoffeeShop)
            .where(CoffeeShop.latitude.isnot(None))
            .where(CoffeeShop.longitude.isnot(None))
            .order_by(CoffeeShop.name)
        )
        return list(result.scalars().all())

    async def get_top_rated(self, db: AsyncSession, limit: int = 10) -> list[CoffeeShop]:
        """Get top shops, preferring reviewed shops and filling the rest."""
        review_count = func.count(Review.id)
        average_rating = func.avg(Review.rating)
        result = await db.execute(
            select(CoffeeShop)
            .outerjoin(CoffeeShop.reviews)
            .options(*_shop_eager_options())
            .group_by(CoffeeShop.id)
            .order_by(
                (review_count > 0).desc(),
                average_rating.desc().nulls_last(),
                review_count.desc(),
                CoffeeShop.created_at.desc(),
                CoffeeShop.name,
            )
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def get_distinct_districts(self, db: AsyncSession) -> list[str]:
        """Get all unique districts."""
        result = await db.execute(
            select(CoffeeShop.district)
            .where(CoffeeShop.district.isnot(None))
            .distinct()
            .order_by(CoffeeShop.district)
        )
        return [row[0] for row in result.all()]

    async def get_distinct_purposes(self, db: AsyncSession) -> list[str]:
        """Get all unique purposes."""
        result = await db.execute(
            select(ShopPurpose.purpose).distinct().order_by(ShopPurpose.purpose)
        )
        return [row[0] for row in result.all()]

    async def get_distinct_spaces(self, db: AsyncSession) -> list[str]:
        """Get all unique space types."""
        result = await db.execute(
            select(ShopSpace.space_type).distinct().order_by(ShopSpace.space_type)
        )
        return [row[0] for row in result.all()]

    async def get_distinct_amenities(self, db: AsyncSession) -> list[str]:
        """Get all unique amenities."""
        result = await db.execute(
            select(ShopAmenity.amenity).distinct().order_by(ShopAmenity.amenity)
        )
        return [row[0] for row in result.all()]


shop_repository = ShopRepository(CoffeeShop)
