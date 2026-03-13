import re
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import CoffeeShop, ShopAmenity, ShopPurpose, ShopSpace, ShopStatus
from app.schemas import CoffeeShopCreate, CoffeeShopUpdate


def _slugify(text: str) -> str:
    """Convert Vietnamese text to URL-friendly slug."""
    # Vietnamese character map
    char_map = {
        "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
        "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
        "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
        "đ": "d",
        "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
        "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
        "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
        "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
        "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
        "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
        "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
        "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
        "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
    }

    text = text.lower()
    result = []
    for char in text:
        result.append(char_map.get(char, char))
    text = "".join(result)

    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


async def get_shops(
    db: AsyncSession,
    search: Optional[str] = None,
    district: Optional[list[str]] = None,
    purpose: Optional[list[str]] = None,
    space: Optional[list[str]] = None,
    amenity: Optional[list[str]] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 30,
) -> tuple[list[CoffeeShop], int]:
    """Get shops with filters and pagination."""
    query = select(CoffeeShop).options(
        selectinload(CoffeeShop.purposes),
        selectinload(CoffeeShop.spaces),
        selectinload(CoffeeShop.amenities),
    )
    count_query = select(func.count(func.distinct(CoffeeShop.id)))

    # Apply search filter (Searching name, address, and district)
    if search:
        search_filter = (
            CoffeeShop.name.ilike(f"%{search}%") |
            CoffeeShop.address.ilike(f"%{search}%") |
            CoffeeShop.district.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if district:
        # Match Any of the districts
        district_filter = CoffeeShop.district.in_(district)
        query = query.where(district_filter)
        count_query = count_query.where(district_filter)

    if status:
        query = query.where(CoffeeShop.status == status)
        count_query = count_query.where(CoffeeShop.status == status)

    if purpose:
        query = query.join(CoffeeShop.purposes).where(
            ShopPurpose.purpose.in_(purpose)
        )
        count_query = (
            count_query.join(ShopPurpose, CoffeeShop.id == ShopPurpose.shop_id)
            .where(ShopPurpose.purpose.in_(purpose))
        )

    if space:
        query = query.join(CoffeeShop.spaces).where(
            ShopSpace.space_type.in_(space)
        )
        count_query = (
            count_query.join(ShopSpace, CoffeeShop.id == ShopSpace.shop_id)
            .where(ShopSpace.space_type.in_(space))
        )

    if amenity:
        query = query.join(CoffeeShop.amenities).where(
            ShopAmenity.amenity.in_(amenity)
        )
        count_query = (
            count_query.join(ShopAmenity, CoffeeShop.id == ShopAmenity.shop_id)
            .where(ShopAmenity.amenity.in_(amenity))
        )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * limit
    query = query.order_by(CoffeeShop.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    shops = result.unique().scalars().all()

    return shops, total


async def get_shop_by_id(db: AsyncSession, shop_id: int) -> Optional[CoffeeShop]:
    """Get a single shop by ID."""
    query = (
        select(CoffeeShop)
        .options(
            selectinload(CoffeeShop.purposes),
            selectinload(CoffeeShop.spaces),
            selectinload(CoffeeShop.amenities),
        )
        .where(CoffeeShop.id == shop_id)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_shop_by_slug(db: AsyncSession, slug: str) -> Optional[CoffeeShop]:
    """Get a single shop by slug."""
    query = (
        select(CoffeeShop)
        .options(
            selectinload(CoffeeShop.purposes),
            selectinload(CoffeeShop.spaces),
            selectinload(CoffeeShop.amenities),
        )
        .where(CoffeeShop.slug == slug)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def create_shop(db: AsyncSession, shop_data: CoffeeShopCreate) -> CoffeeShop:
    """Create a new coffee shop."""
    slug = _slugify(shop_data.name)

    # Ensure unique slug
    existing = await db.execute(
        select(CoffeeShop).where(CoffeeShop.slug == slug)
    )
    if existing.scalar_one_or_none():
        # Append a counter
        counter = 1
        while True:
            new_slug = f"{slug}-{counter}"
            existing = await db.execute(
                select(CoffeeShop).where(CoffeeShop.slug == new_slug)
            )
            if not existing.scalar_one_or_none():
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

    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    # Reload with relationships
    return await get_shop_by_id(db, shop.id)


async def update_shop(
    db: AsyncSession, shop_id: int, shop_data: CoffeeShopUpdate
) -> Optional[CoffeeShop]:
    """Update an existing coffee shop."""
    shop = await get_shop_by_id(db, shop_id)
    if not shop:
        return None

    update_data = shop_data.model_dump(exclude_unset=True)

    # Handle relationships separately
    purposes = update_data.pop("purposes", None)
    spaces = update_data.pop("spaces", None)
    amenities = update_data.pop("amenities", None)

    # Update simple fields
    for key, value in update_data.items():
        setattr(shop, key, value)

    # Update name → regenerate slug
    if "name" in update_data:
        shop.slug = _slugify(update_data["name"])

    # Update relationships
    if purposes is not None:
        # Clear existing and add new
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

    await db.commit()
    return await get_shop_by_id(db, shop_id)


async def delete_shop(db: AsyncSession, shop_id: int) -> bool:
    """Delete a coffee shop."""
    shop = await get_shop_by_id(db, shop_id)
    if not shop:
        return False

    await db.delete(shop)
    await db.commit()
    return True


async def get_distinct_districts(db: AsyncSession) -> list[str]:
    """Get all unique districts."""
    result = await db.execute(
        select(CoffeeShop.district)
        .where(CoffeeShop.district.isnot(None))
        .distinct()
        .order_by(CoffeeShop.district)
    )
    return [row[0] for row in result.all()]


async def get_distinct_purposes(db: AsyncSession) -> list[str]:
    """Get all unique purposes."""
    result = await db.execute(
        select(ShopPurpose.purpose).distinct().order_by(ShopPurpose.purpose)
    )
    return [row[0] for row in result.all()]


async def get_distinct_spaces(db: AsyncSession) -> list[str]:
    """Get all unique space types."""
    result = await db.execute(
        select(ShopSpace.space_type).distinct().order_by(ShopSpace.space_type)
    )
    return [row[0] for row in result.all()]


async def get_distinct_amenities(db: AsyncSession) -> list[str]:
    """Get all unique amenities."""
    result = await db.execute(
        select(ShopAmenity.amenity).distinct().order_by(ShopAmenity.amenity)
    )
    return [row[0] for row in result.all()]


async def create_suggestion(
    db: AsyncSession, suggestion_data: CoffeeShopCreate
) -> CoffeeShop:
    """Create a new shop suggestion."""
    from app.models import ShopSuggestion
    
    suggestion = ShopSuggestion(
        shop_name=suggestion_data.shop_name,
        address=suggestion_data.address,
        district=suggestion_data.district,
        reason=suggestion_data.reason,
        contributor_name=suggestion_data.contributor_name,
        contributor_email=suggestion_data.contributor_email,
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)
    return suggestion
