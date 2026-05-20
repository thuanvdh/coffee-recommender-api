import asyncio
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.utils import slugify_vietnamese

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def upload_suggestion_image(file: UploadFile, shop_name: str) -> str:
    """Upload a suggestion cover image to Cloudinary and return its secure URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ảnh quán phải là JPG, PNG hoặc WEBP",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng chọn ảnh quán để tải lên",
        )
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ảnh quán không được vượt quá 5MB",
        )

    if not (
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary chưa được cấu hình trên máy chủ",
        )

    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary SDK chưa được cài đặt trên máy chủ",
        ) from exc

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    public_id = f"{slugify_vietnamese(shop_name) or 'suggestion'}-{uuid4().hex[:10]}"
    try:
        response = await asyncio.to_thread(
            cloudinary.uploader.upload,
            image_bytes,
            folder="danang_coffee/suggestions",
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Không thể tải ảnh lên Cloudinary. Vui lòng thử lại sau",
        ) from exc

    secure_url = response.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary không trả về URL ảnh",
        )
    return secure_url
