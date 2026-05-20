"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.models import User
from app.security import get_password_hash


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user):
    """Test successful admin login returns JWT token."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "testadmin", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "testadmin"
    assert data["is_admin"] is True


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user):
    """Test login with wrong password returns 401."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "testadmin", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user returns 401."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "nobody", "password": "nopassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_non_admin_forbidden(client: AsyncClient, db_session):
    """Test non-admin users cannot access the admin login flow."""
    user = User(
        username="regular",
        email="regular@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": "regular", "password": "testpassword"},
    )
    assert response.status_code == 403
