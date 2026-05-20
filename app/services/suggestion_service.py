import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CoffeeShop, ShopSuggestion
from app.repositories.suggestion_repository import suggestion_repository
from app.schemas import CoffeeShopCreate, CoffeeShopUpdate, ShopSuggestionCreate
from app.services.shop_service import shop_service


class SuggestionService:
    """Business logic for shop suggestion workflow."""

    def __init__(self):
        self.repository = suggestion_repository

    async def create_suggestion(
        self, db: AsyncSession, suggestion_data: ShopSuggestionCreate
    ) -> ShopSuggestion:
        """Create a new shop suggestion."""
        json_payload = {
            "purposes": suggestion_data.purposes,
            "spaces": suggestion_data.spaces,
            "amenities": suggestion_data.amenities,
            "drinks": [d.model_dump() for d in suggestion_data.drinks],
        }

        suggestion = ShopSuggestion(
            shop_id=getattr(suggestion_data, "shop_id", None),
            shop_name=suggestion_data.shop_name,
            address=suggestion_data.address,
            district=suggestion_data.district,
            phone=suggestion_data.phone,
            image_url=suggestion_data.image_url,
            description=suggestion_data.description,
            opening_hours=suggestion_data.opening_hours,
            price_range=suggestion_data.price_range,
            json_data=json.dumps(json_payload),
            reason=suggestion_data.reason,
            contributor_name=suggestion_data.contributor_name,
            contributor_email=suggestion_data.contributor_email,
            status="pending",
        )
        db.add(suggestion)
        await db.commit()
        await db.refresh(suggestion)
        return suggestion

    async def get_suggestions(
        self, db: AsyncSession, status: Optional[str] = None
    ) -> list[ShopSuggestion]:
        """Get all suggestions, optionally filtered by status."""
        return await self.repository.get_by_status(db, status=status)

    async def get_suggestion_by_id(
        self, db: AsyncSession, suggestion_id: int
    ) -> Optional[ShopSuggestion]:
        """Get a single suggestion by ID."""
        return await self.repository.get_by_id(db, suggestion_id)

    async def approve_suggestion(
        self, db: AsyncSession, suggestion_id: int
    ) -> Optional[CoffeeShop]:
        """Approve a suggestion and create/update the corresponding shop."""
        suggestion = await self.repository.get_by_id(db, suggestion_id)
        if not suggestion or suggestion.status != "pending":
            return None

        data = json.loads(suggestion.json_data or "{}")

        if suggestion.shop_id:
            # Update existing shop
            shop_update = CoffeeShopUpdate(
                name=suggestion.shop_name,
                address=suggestion.address,
                district=suggestion.district,
                phone=suggestion.phone,
                image_url=suggestion.image_url,
                description=suggestion.description,
                opening_hours=suggestion.opening_hours,
                price_range=suggestion.price_range,
                purposes=data.get("purposes"),
                spaces=data.get("spaces"),
                amenities=data.get("amenities"),
                drinks=data.get("drinks"),
            )
            shop = await shop_service.update_shop(db, suggestion.shop_id, shop_update)
        else:
            # Create new shop
            shop_create = CoffeeShopCreate(
                name=suggestion.shop_name,
                address=suggestion.address,
                district=suggestion.district,
                phone=suggestion.phone,
                image_url=suggestion.image_url,
                description=suggestion.description,
                opening_hours=suggestion.opening_hours,
                price_range=suggestion.price_range,
                status="new",
                purposes=data.get("purposes", []),
                spaces=data.get("spaces", []),
                amenities=data.get("amenities", []),
                drinks=data.get("drinks", []),
            )
            shop = await shop_service.create_shop(db, shop_create)

        if shop:
            suggestion.status = "approved"
            await db.commit()
            await db.refresh(suggestion)

        return shop

    async def reject_suggestion(self, db: AsyncSession, suggestion_id: int) -> bool:
        """Reject a pending suggestion."""
        suggestion = await self.repository.get_by_id(db, suggestion_id)
        if not suggestion or suggestion.status != "pending":
            return False

        suggestion.status = "rejected"
        await db.commit()
        return True


suggestion_service = SuggestionService()
