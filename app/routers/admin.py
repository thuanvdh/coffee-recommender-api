from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app import crud
from app.database import get_db
from app.schemas import ShopSuggestionResponse, CoffeeShopResponse, ShopSuggestionApprove

router = APIRouter(prefix="/api/admin/suggestions", tags=["Admin Suggestions"])

@router.get("", response_model=list[ShopSuggestionResponse])
async def list_suggestions(
    status: Optional[str] = None, 
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách đề xuất."""
    return await crud.get_suggestions(db, status=status)

@router.get("/{suggestion_id}", response_model=ShopSuggestionResponse)
async def get_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db)):
    """Lấy chi tiết đề xuất."""
    suggestion = await crud.get_suggestion_by_id(db, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    return suggestion

@router.post("/{suggestion_id}/approve", response_model=CoffeeShopResponse)
async def approve_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db)):
    """Phê duyệt đề xuất."""
    shop = await crud.approve_suggestion(db, suggestion_id)
    if not shop:
        raise HTTPException(status_code=400, detail="Không thể phê duyệt đề xuất này")
    return shop

@router.post("/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db)):
    """Từ chối đề xuất."""
    success = await crud.reject_suggestion(db, suggestion_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể từ chối đề xuất này")
    return {"message": "Đã từ chối đề xuất"}
