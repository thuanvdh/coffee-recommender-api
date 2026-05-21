from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User
from app.schemas import CoffeeShopResponse, ShopSuggestionResponse, CoffeeShopListResponse
from app.serializers import shop_to_response, suggestion_to_response
from app.services.suggestion_service import suggestion_service
from app.services.shop_service import shop_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/suggestions", response_model=list[ShopSuggestionResponse])
async def list_suggestions(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Lấy danh sách đề xuất. Yêu cầu quyền admin."""
    suggestions = await suggestion_service.get_suggestions(db, status=status)
    return [suggestion_to_response(s) for s in suggestions]


@router.get("/suggestions/{suggestion_id}", response_model=ShopSuggestionResponse)
async def get_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Lấy chi tiết đề xuất. Yêu cầu quyền admin."""
    suggestion = await suggestion_service.get_suggestion_by_id(db, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    return suggestion_to_response(suggestion)


@router.post("/suggestions/{suggestion_id}/approve", response_model=CoffeeShopResponse)
async def approve_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Phê duyệt đề xuất. Yêu cầu quyền admin."""
    shop = await suggestion_service.approve_suggestion(db, suggestion_id)
    if not shop:
        raise HTTPException(
            status_code=400, detail="Không thể phê duyệt đề xuất này"
        )
    return shop_to_response(shop)


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Từ chối đề xuất. Yêu cầu quyền admin."""
    success = await suggestion_service.reject_suggestion(db, suggestion_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Không thể từ chối đề xuất này"
        )
    return {"message": "Đã từ chối đề xuất"}


@router.get("/shops", response_model=CoffeeShopListResponse)
async def list_admin_shops(
    search: Optional[str] = Query(None, description="Tìm theo tên quán"),
    page: int = Query(1, ge=1, description="Trang"),
    limit: int = Query(25, ge=1, le=100, description="Số lượng mỗi trang"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Lấy danh sách tất cả các quán cà phê (có phân trang). Yêu cầu quyền admin."""
    shops, total = await shop_service.list_shops(
        db,
        search=search,
        page=page,
        limit=limit,
    )
    return CoffeeShopListResponse(
        total=total,
        page=page,
        limit=limit,
        shops=[shop_to_response(s) for s in shops],
    )
