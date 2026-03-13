from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import ShopSuggestionCreate, ShopSuggestionResponse

router = APIRouter(prefix="/api/suggestions", tags=["Suggestions"])


@router.post("", response_model=ShopSuggestionResponse, status_code=status.HTTP_201_CREATED)
async def create_suggestion(
    suggestion_data: ShopSuggestionCreate, db: AsyncSession = Depends(get_db)
):
    """Gửi một đề xuất quán cà phê mới."""
    return await crud.create_suggestion(db, suggestion_data)
