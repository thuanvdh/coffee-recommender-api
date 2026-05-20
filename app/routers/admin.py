from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User
from app.schemas import CoffeeShopResponse, ShopSuggestionResponse
from app.serializers import shop_to_response
from app.services.suggestion_service import suggestion_service

router = APIRouter(prefix="/api/admin/suggestions", tags=["Admin Suggestions"])


@router.get("", response_model=list[ShopSuggestionResponse])
async def list_suggestions(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Lấy danh sách đề xuất. Yêu cầu quyền admin."""
    return await suggestion_service.get_suggestions(db, status=status)


@router.get("/{suggestion_id}", response_model=ShopSuggestionResponse)
async def get_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Lấy chi tiết đề xuất. Yêu cầu quyền admin."""
    suggestion = await suggestion_service.get_suggestion_by_id(db, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    return suggestion


@router.post("/{suggestion_id}/approve", response_model=CoffeeShopResponse)
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


@router.post("/{suggestion_id}/reject")
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
