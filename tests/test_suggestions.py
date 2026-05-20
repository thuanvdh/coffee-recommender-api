"""Tests for suggestion endpoints."""

import pytest
from httpx import AsyncClient

from app.routers import suggestions as suggestions_router


@pytest.mark.asyncio
async def test_create_suggestion(client: AsyncClient):
    """Test creating a new suggestion."""
    suggestion_data = {
        "shop_name": "Suggested Coffee",
        "address": "789 Suggestion Rd",
        "district": "Sơn Trà",
        "purposes": ["Tụ tập bạn bè"],
        "spaces": ["Sân vườn"],
        "amenities": ["Chỗ đậu xe"],
        "drinks": [],
        "reason": "Quán rất hay",
        "contributor_name": "Tester",
        "contributor_email": "test@example.com",
    }
    response = await client.post("/api/suggestions", json=suggestion_data)
    assert response.status_code == 201
    data = response.json()
    assert data["shop_name"] == "Suggested Coffee"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_suggestion_with_image_uploads_and_saves_url(
    client: AsyncClient, monkeypatch
):
    """Test creating a suggestion with an uploaded image stores the Cloudinary URL."""

    async def fake_upload(file, shop_name):
        assert shop_name == "Image Coffee"
        assert file.filename == "shop.webp"
        return "https://res.cloudinary.com/demo/image/upload/suggestions/shop.webp"

    monkeypatch.setattr(suggestions_router, "upload_suggestion_image", fake_upload)
    response = await client.post(
        "/api/suggestions/with-image",
        data={
            "shop_name": "Image Coffee",
            "address": "123 Image Street",
            "district": "Hải Châu",
            "reason": "Quán có ảnh đẹp",
        },
        files={"image": ("shop.webp", b"fake-image", "image/webp")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["shop_name"] == "Image Coffee"
    assert data["image_url"] == "https://res.cloudinary.com/demo/image/upload/suggestions/shop.webp"


@pytest.mark.asyncio
async def test_admin_list_suggestions_unauthorized(client: AsyncClient):
    """Test that listing suggestions without auth returns 401."""
    response = await client.get("/api/admin/suggestions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_suggestions_authorized(
    client: AsyncClient, admin_token: str
):
    """Test that admin can list suggestions with valid token."""
    response = await client.get(
        "/api/admin/suggestions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_approve_unauthorized(client: AsyncClient):
    """Test that approving without auth returns 401."""
    response = await client.post("/api/admin/suggestions/1/approve")
    assert response.status_code == 401
