from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from fastapi.responses import RedirectResponse
from app.security import verify_password

from app.models import CoffeeShop, ShopPurpose, ShopSpace, ShopAmenity, ShopSuggestion, User
from app.config import settings


class CoffeeShopAdmin(ModelView, model=CoffeeShop):
    column_list = [CoffeeShop.id, CoffeeShop.name, CoffeeShop.slug, CoffeeShop.status]
    column_searchable_list = [CoffeeShop.name, CoffeeShop.slug]
    column_filters = [CoffeeShop.status, CoffeeShop.district]
    name = "Quán Cà Phê"
    name_plural = "Quán Cà Phê"
    icon = "fa-solid fa-mug-hot"


class PurposeAdmin(ModelView, model=ShopPurpose):
    column_list = [ShopPurpose.id, ShopPurpose.shop_id, ShopPurpose.purpose]
    name = "Mục đích"
    name_plural = "Mục đích"
    icon = "fa-solid fa-bullseye"


class SpaceAdmin(ModelView, model=ShopSpace):
    column_list = [ShopSpace.id, ShopSpace.shop_id, ShopSpace.space_type]
    name = "Không gian"
    name_plural = "Không gian"
    icon = "fa-solid fa-couch"


class AmenityAdmin(ModelView, model=ShopAmenity):
    column_list = [ShopAmenity.id, ShopAmenity.shop_id, ShopAmenity.amenity]
    name = "Tiện ích"
    name_plural = "Tiện ích"
    icon = "fa-solid fa-wifi"


class SuggestionAdmin(ModelView, model=ShopSuggestion):
    column_list = [ShopSuggestion.id, ShopSuggestion.shop_name, ShopSuggestion.status, ShopSuggestion.created_at]
    column_filters = [ShopSuggestion.status]
    name_plural = "Đề xuất"
    icon = "fa-solid fa-lightbulb"


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.is_active, User.is_superuser]
    column_searchable_list = [User.username, User.email]
    column_filters = [User.is_active, User.is_superuser]
    name = "Người dùng"
    name_plural = "Người dùng"
    icon = "fa-solid fa-users"


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        from sqlalchemy import select
        from app.database import async_session

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if user and verify_password(password, user.hashed_password) and user.is_superuser:
                request.session.update({"token": "authenticated", "user_id": user.id})
                return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
