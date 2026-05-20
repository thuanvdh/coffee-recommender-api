from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ShopSuggestion
from app.repositories.base import BaseRepository
from app.schemas import ShopSuggestionCreate, ShopSuggestionCreate as ShopSuggestionUpdate


class SuggestionRepository(BaseRepository[ShopSuggestion, ShopSuggestionCreate, ShopSuggestionUpdate]):
    """Repository for ShopSuggestion data access."""

    async def get_by_id(self, db: AsyncSession, suggestion_id: int) -> Optional[ShopSuggestion]:
        """Get a single suggestion by ID."""
        query = select(ShopSuggestion).where(ShopSuggestion.id == suggestion_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self, db: AsyncSession, status: Optional[str] = None
    ) -> list[ShopSuggestion]:
        """Get suggestions filtered by status, ordered by newest first."""
        query = select(ShopSuggestion).order_by(ShopSuggestion.created_at.desc())
        if status:
            query = query.where(ShopSuggestion.status == status)
        result = await db.execute(query)
        return list(result.scalars().all())


suggestion_repository = SuggestionRepository(ShopSuggestion)
