import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class ShopStatus(str, enum.Enum):
    OPEN = "open"
    NEW = "new"
    CLOSED_TEMP = "closed_temp"
    CLOSED_PERMANENT = "closed_permanent"


class CoffeeShop(Base):
    __tablename__ = "coffee_shops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)
    district = Column(String(100), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    opening_hours = Column(String(100), nullable=True)
    price_range = Column(String(50), nullable=True)
    status = Column(
        String(30), default=ShopStatus.OPEN.value, nullable=False, index=True
    )
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        nullable=False,
    )

    # Relationships
    purposes = relationship(
        "ShopPurpose", back_populates="shop", cascade="all, delete-orphan"
    )
    spaces = relationship(
        "ShopSpace", back_populates="shop", cascade="all, delete-orphan"
    )
    amenities = relationship(
        "ShopAmenity", back_populates="shop", cascade="all, delete-orphan"
    )
    drinks = relationship(
        "ShopDrink", back_populates="shop", cascade="all, delete-orphan"
    )
    images = relationship(
        "ShopImage", back_populates="shop", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", back_populates="shop", cascade="all, delete-orphan"
    )


class ShopPurpose(Base):
    __tablename__ = "shop_purposes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(
        Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"), nullable=False
    )
    purpose = Column(String(100), nullable=False, index=True)

    shop = relationship("CoffeeShop", back_populates="purposes")


class ShopSpace(Base):
    __tablename__ = "shop_spaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(
        Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"), nullable=False
    )
    space_type = Column(String(100), nullable=False, index=True)

    shop = relationship("CoffeeShop", back_populates="spaces")


class ShopAmenity(Base):
    __tablename__ = "shop_amenities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(
        Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"), nullable=False
    )
    amenity = Column(String(100), nullable=False, index=True)

    shop = relationship("CoffeeShop", back_populates="amenities")


class ShopDrink(Base):
    __tablename__ = "shop_drinks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(
        Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    price = Column(String(50), nullable=True)
    category = Column(String(50), default="drink")
    is_signature = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False)

    shop = relationship("CoffeeShop", back_populates="drinks")


class ShopImage(Base):
    __tablename__ = "shop_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(
        Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)

    shop = relationship("CoffeeShop", back_populates="images")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(
        Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"), nullable=False
    )
    user_name = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False, default=5)
    comment = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )

    shop = relationship("CoffeeShop", back_populates="reviews")


class ShopSuggestion(Base):
    __tablename__ = "shop_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("coffee_shops.id", ondelete="SET NULL"), nullable=True) # If updating existing
    shop_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    district = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    opening_hours = Column(String(100), nullable=True)
    price_range = Column(String(50), nullable=True)
    
    # New fields for complex data
    json_data = Column(Text, nullable=True) # Stores purposes, spaces, amenities, drinks as JSON
    
    reason = Column(Text, nullable=True)
    contributor_name = Column(String(255), nullable=True)
    contributor_email = Column(String(255), nullable=True)
    status = Column(String(30), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    target_shop = relationship("CoffeeShop", foreign_keys=[shop_id])


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
