from app.schemas import CoffeeShopResponse


def shop_to_response(shop) -> CoffeeShopResponse:
    """Convert a CoffeeShop ORM object with loaded relationships to API shape."""
    return CoffeeShopResponse(
        id=shop.id,
        name=shop.name,
        slug=shop.slug,
        address=shop.address,
        district=shop.district,
        phone=shop.phone,
        image_url=shop.image_url,
        description=shop.description,
        opening_hours=shop.opening_hours,
        price_range=shop.price_range,
        status=shop.status,
        latitude=shop.latitude,
        longitude=shop.longitude,
        distance_km=getattr(shop, "distance_km", None),
        purposes=[p.purpose for p in shop.purposes],
        spaces=[s.space_type for s in shop.spaces],
        amenities=[a.amenity for a in shop.amenities],
        drinks=[
            {
                "id": d.id,
                "name": d.name,
                "price": d.price,
                "category": d.category,
                "is_signature": d.is_signature,
                "is_trending": d.is_trending,
            }
            for d in shop.drinks
        ],
        images=[
            {"id": img.id, "url": img.url, "alt_text": img.alt_text}
            for img in shop.images
        ],
        reviews=[
            {
                "id": r.id,
                "user_name": r.user_name,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at,
            }
            for r in shop.reviews
        ],
        created_at=shop.created_at,
        updated_at=shop.updated_at,
    )
