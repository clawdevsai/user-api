"""Integration test: quickstart.md scenario 5 (admin-only paginated listing)."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.http.conftest import create_user, make_authenticated_override
from user_api.adapters.inbound.http import deps
from user_api.adapters.inbound.http.main import app
from user_api.domain.entities.user import Role


async def test_admin_lists_users_paginated(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(
        db_session, "admin@x.com", "Senha123!", roles=frozenset({Role.USER, Role.ADMIN})
    )
    await create_user(db_session, "u1@x.com", "Senha123!")
    await create_user(db_session, "u2@x.com", "Senha123!")
    app.dependency_overrides[deps.get_current_user] = make_authenticated_override(admin)

    response = await client.get("/users?page=1&page_size=20")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert all("password_hash" not in item for item in body["items"])


async def test_regular_user_cannot_list_users(client: AsyncClient, db_session: AsyncSession):
    regular_user = await create_user(db_session, "u@x.com", "Senha123!")
    app.dependency_overrides[deps.get_current_user] = make_authenticated_override(regular_user)

    response = await client.get("/users?page=1&page_size=20")

    assert response.status_code == 403
