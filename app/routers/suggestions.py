from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ShopSuggestionCreate, ShopSuggestionResponse
from app.services.cloudinary_service import upload_suggestion_image
from app.services.suggestion_service import suggestion_service

router = APIRouter(prefix="/api/suggestions", tags=["Suggestions"])


@router.post("", response_model=ShopSuggestionResponse, status_code=status.HTTP_201_CREATED)
async def create_suggestion(
    suggestion_data: ShopSuggestionCreate, db: AsyncSession = Depends(get_db)
):
    """Gửi một đề xuất quán cà phê mới."""
    return await suggestion_service.create_suggestion(db, suggestion_data)


@router.post("/with-image", response_model=ShopSuggestionResponse, status_code=status.HTTP_201_CREATED)
async def create_suggestion_with_image(
    shop_name: str = Form(...),
    district: str | None = Form(None),
    address: str | None = Form(None),
    phone: str | None = Form(None),
    description: str | None = Form(None),
    opening_hours: str | None = Form(None),
    price_range: str | None = Form(None),
    reason: str | None = Form(None),
    contributor_name: str | None = Form(None),
    contributor_email: str | None = Form(None),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Gửi đề xuất quán mới kèm ảnh, lưu ảnh lên Cloudinary trước."""
    image_url = await upload_suggestion_image(image, shop_name)
    suggestion_data = ShopSuggestionCreate(
        shop_name=shop_name,
        district=district,
        address=address,
        phone=phone,
        image_url=image_url,
        description=description,
        opening_hours=opening_hours,
        price_range=price_range,
        reason=reason,
        contributor_name=contributor_name,
        contributor_email=contributor_email,
    )
    return await suggestion_service.create_suggestion(db, suggestion_data)
