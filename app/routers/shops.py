from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.models import ShopStatus
from app.schemas import (
    CoffeeShopCreate,
    CoffeeShopListResponse,
    CoffeeShopResponse,
    CoffeeShopUpdate,
    FilterOptionsResponse,
)

router = APIRouter(prefix="/api", tags=["Coffee Shops"])


def _shop_to_response(shop) -> CoffeeShopResponse:
    """Convert ORM shop to response schema."""
    return CoffeeShopResponse(
        id=shop.id,
        name=shop.name,
        slug=shop.slug,
        address=shop.address,
        district=shop.district,
        phone=shop.phone,
        image_url=shop.image_url,
        description=shop.description,
        opening_hours=shop.opening_hours,
        price_range=shop.price_range,
        status=shop.status,
        latitude=shop.latitude,
        longitude=shop.longitude,
        purposes=[p.purpose for p in shop.purposes],
        spaces=[s.space_type for s in shop.spaces],
        amenities=[a.amenity for a in shop.amenities],
        created_at=shop.created_at,
        updated_at=shop.updated_at,
    )


@router.get("/shops", response_model=CoffeeShopListResponse)
async def list_shops(
    search: Optional[str] = Query(None, description="Tìm theo tên quán"),
    district: Optional[list[str]] = Query(None, description="Lọc theo quận"),
    purpose: Optional[list[str]] = Query(None, description="Lọc theo loại hình"),
    space: Optional[list[str]] = Query(None, description="Lọc theo không gian"),
    amenity: Optional[list[str]] = Query(None, description="Lọc theo tiện ích"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    page: int = Query(1, ge=1, description="Trang"),
    limit: int = Query(25, ge=1, le=100, description="Số lượng mỗi trang"),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách quán cà phê với bộ lọc và phân trang."""
    shops, total = await crud.get_shops(
        db,
        search=search,
        district=district,
        purpose=purpose,
        space=space,
        amenity=amenity,
        status=status,
        page=page,
        limit=limit,
    )
    return CoffeeShopListResponse(
        total=total,
        page=page,
        limit=limit,
        shops=[_shop_to_response(s) for s in shops],
    )


@router.get("/shops/{shop_id}", response_model=CoffeeShopResponse)
async def get_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Lấy chi tiết một quán cà phê."""
    shop = await crud.get_shop_by_id(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán cà phê")
    return _shop_to_response(shop)


@router.get("/shops/slug/{slug}", response_model=CoffeeShopResponse)
async def get_shop_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Lấy chi tiết một quán cà phê theo slug."""
    shop = await crud.get_shop_by_slug(db, slug)
    if not shop:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán cà phê")
    return _shop_to_response(shop)


@router.post("/shops", response_model=CoffeeShopResponse, status_code=201)
async def create_shop(
    shop_data: CoffeeShopCreate, db: AsyncSession = Depends(get_db)
):
    """Tạo quán cà phê mới."""
    shop = await crud.create_shop(db, shop_data)
    return _shop_to_response(shop)


@router.put("/shops/{shop_id}", response_model=CoffeeShopResponse)
async def update_shop(
    shop_id: int,
    shop_data: CoffeeShopUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật thông tin quán cà phê."""
    shop = await crud.update_shop(db, shop_id, shop_data)
    if not shop:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán cà phê")
    return _shop_to_response(shop)


@router.delete("/shops/{shop_id}", status_code=204)
async def delete_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Xóa quán cà phê."""
    deleted = await crud.delete_shop(db, shop_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán cà phê")
    return None


@router.get("/districts", response_model=list[str])
async def list_districts(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách quận."""
    return await crud.get_distinct_districts(db)


@router.get("/purposes", response_model=list[str])
async def list_purposes(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách loại hình."""
    return await crud.get_distinct_purposes(db)


@router.get("/spaces", response_model=list[str])
async def list_spaces(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách không gian."""
    return await crud.get_distinct_spaces(db)


@router.get("/amenities", response_model=list[str])
async def list_amenities(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách tiện ích."""
    return await crud.get_distinct_amenities(db)


@router.get("/filters", response_model=FilterOptionsResponse)
async def get_filter_options(db: AsyncSession = Depends(get_db)):
    """Lấy tất cả các tùy chọn bộ lọc."""
    return FilterOptionsResponse(
        districts=await crud.get_distinct_districts(db),
        purposes=await crud.get_distinct_purposes(db),
        spaces=await crud.get_distinct_spaces(db),
        amenities=await crud.get_distinct_amenities(db),
    )
