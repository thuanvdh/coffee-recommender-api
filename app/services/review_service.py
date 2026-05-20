from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Review
from app.repositories.review_repository import review_repository
from app.schemas import ReviewCreate


class ReviewService:
    """Business logic for review operations."""

    def __init__(self):
        self.repository = review_repository

    async def create_review(
        self, db: AsyncSession, shop_id: int, review_data: ReviewCreate
    ) -> Review:
        """Create a new review for a shop."""
        review = await self.repository.create_for_shop(db, shop_id, review_data)
        await db.commit()
        return review


review_service = ReviewService()
