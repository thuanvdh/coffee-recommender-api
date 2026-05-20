from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Review
from app.repositories.base import BaseRepository
from app.schemas import ReviewCreate, ReviewCreate as ReviewUpdate


class ReviewRepository(BaseRepository[Review, ReviewCreate, ReviewUpdate]):
    """Repository for Review data access."""

    async def create_for_shop(
        self, db: AsyncSession, shop_id: int, review_data: ReviewCreate
    ) -> Review:
        """Create a new review for a specific shop."""
        review = Review(
            shop_id=shop_id,
            user_name=review_data.user_name,
            rating=review_data.rating,
            comment=review_data.comment,
        )
        db.add(review)
        await db.flush()
        await db.refresh(review)
        return review


review_repository = ReviewRepository(Review)
