"""Tests for coffee shop endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_shops_empty(client: AsyncClient):
    """Test listing shops when database is empty."""
    response = await client.get("/api/shops")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["shops"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_create_shop(client: AsyncClient):
    """Test creating a new shop."""
    shop_data = {
        "name": "Test Coffee Shop",
        "address": "123 Test Street",
        "district": "Hải Châu",
        "opening_hours": "07:00 - 22:00",
        "price_range": "30k - 60k",
        "purposes": ["Ngồi làm việc"],
        "spaces": ["Trong nhà"],
        "amenities": ["Wifi miễn phí"],
        "drinks": [
            {"name": "Cà phê sữa đá", "price": "29,000đ", "category": "drink"}
        ],
    }
    response = await client.post("/api/shops", json=shop_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Coffee Shop"
    assert data["slug"] == "test-coffee-shop"
    assert data["district"] == "Hải Châu"
    assert len(data["drinks"]) == 1


@pytest.mark.asyncio
async def test_get_shop_by_slug(client: AsyncClient):
    """Test getting a shop by its slug after creation."""
    # Create a shop first
    shop_data = {
        "name": "Slug Test Shop",
        "address": "456 Slug Ave",
        "district": "Thanh Khê",
        "purposes": [],
        "spaces": [],
        "amenities": [],
        "drinks": [],
    }
    create_response = await client.post("/api/shops", json=shop_data)
    assert create_response.status_code == 201

    # Get by slug
    response = await client.get("/api/shops/slug/slug-test-shop")
    assert response.status_code == 200
    assert response.json()["name"] == "Slug Test Shop"


@pytest.mark.asyncio
async def test_get_shop_not_found(client: AsyncClient):
    """Test 404 when shop doesn't exist."""
    response = await client.get("/api/shops/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_filters(client: AsyncClient):
    """Test getting filter options."""
    response = await client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    assert "districts" in data
    assert "purposes" in data
    assert "spaces" in data
    assert "amenities" in data


@pytest.mark.asyncio
async def test_get_map_shops_returns_lightweight_locations(client: AsyncClient):
    """Test map endpoint returns only shops with coordinates."""
    located_shop = {
        "name": "Map Coffee",
        "address": "1 Map Street",
        "district": "Hải Châu",
        "latitude": 16.0544,
        "longitude": 108.2022,
    }
    unlocated_shop = {
        "name": "No Pin Coffee",
        "address": "2 Missing Street",
        "district": "Sơn Trà",
    }
    assert (await client.post("/api/shops", json=located_shop)).status_code == 201
    assert (await client.post("/api/shops", json=unlocated_shop)).status_code == 201

    response = await client.get("/api/shops/map")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Map Coffee"
    assert data[0]["latitude"] == 16.0544
    assert data[0]["longitude"] == 108.2022
    assert "reviews" not in data[0]
    assert "drinks" not in data[0]


@pytest.mark.asyncio
async def test_get_top_rated_shops_uses_review_ranking(client: AsyncClient):
    """Test top-rated endpoint ranks shops on the backend."""
    first = await client.post("/api/shops", json={"name": "Good Coffee"})
    second = await client.post("/api/shops", json={"name": "Great Coffee"})
    unrated = await client.post("/api/shops", json={"name": "No Review Coffee"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert unrated.status_code == 201

    first_id = first.json()["id"]
    second_id = second.json()["id"]
    await client.post(
        f"/api/shops/{first_id}/reviews",
        json={"user_name": "A", "rating": 4, "comment": "Good"},
    )
    await client.post(
        f"/api/shops/{second_id}/reviews",
        json={"user_name": "B", "rating": 5, "comment": "Great"},
    )

    response = await client.get("/api/shops/top-rated?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert [shop["name"] for shop in data] == ["Great Coffee", "Good Coffee"]
    assert all(shop["reviews"] for shop in data)


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
