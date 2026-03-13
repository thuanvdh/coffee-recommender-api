from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models import ShopStatus


# ========== Base Schemas ==========
class PurposeBase(BaseModel):
    purpose: str


class SpaceBase(BaseModel):
    space_type: str


class AmenityBase(BaseModel):
    amenity: str


class DrinkBase(BaseModel):
    name: str
    price: Optional[str] = None
    category: str = "drink"
    is_signature: bool = False
    is_trending: bool = False


# ========== Coffee Shop Schemas ==========
class CoffeeShopBase(BaseModel):
    name: str
    address: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    price_range: Optional[str] = None
    status: ShopStatus = ShopStatus.OPEN
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CoffeeShopCreate(CoffeeShopBase):
    purposes: list[str] = []
    spaces: list[str] = []
    amenities: list[str] = []
    drinks: list[DrinkBase] = []


class CoffeeShopUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    price_range: Optional[str] = None
    status: Optional[ShopStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    purposes: Optional[list[str]] = None
    spaces: Optional[list[str]] = None
    amenities: Optional[list[str]] = None
    drinks: Optional[list[DrinkBase]] = None


class DrinkResponse(DrinkBase):
    id: int

    class Config:
        from_attributes = True


class CoffeeShopResponse(CoffeeShopBase):
    id: int
    slug: str
    purposes: list[str] = []
    spaces: list[str] = []
    amenities: list[str] = []
    drinks: list[DrinkResponse] = []
    distance_km: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoffeeShopListResponse(BaseModel):
    total: int
    page: int
    limit: int
    shops: list[CoffeeShopResponse]


# ========== Filter Options ==========
class FilterOptionsResponse(BaseModel):
    districts: list[str]
    purposes: list[str]
    spaces: list[str]
    amenities: list[str]


# ========== Shop Suggestions ==========
class ShopSuggestionBase(BaseModel):
    shop_id: Optional[int] = None # If updating existing
    shop_name: str
    address: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    price_range: Optional[str] = None
    purposes: list[str] = []
    spaces: list[str] = []
    amenities: list[str] = []
    drinks: list[DrinkBase] = []
    reason: Optional[str] = None
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None


class ShopSuggestionCreate(ShopSuggestionBase):
    pass


class ShopSuggestionResponse(ShopSuggestionBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShopSuggestionApprove(BaseModel):
    status: str # approved or rejected


# ========== User Schemas ==========
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
