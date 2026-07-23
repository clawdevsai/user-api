"""Integration test: quickstart.md scenario 3 (authenticated profile access/update)."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.http.conftest import create_user, make_authenticated_override
from user_api.adapters.inbound.http import deps
from user_api.adapters.inbound.http.main import app


async def test_get_own_profile(client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, "a@x.com", "Senha123!")
    app.dependency_overrides[deps.get_current_user] = make_authenticated_override(user)

    response = await client.get("/users/me")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "a@x.com"
    assert "password_hash" not in body


async def test_update_own_profile_email(client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, "a@x.com", "Senha123!")
    app.dependency_overrides[deps.get_current_user] = make_authenticated_override(user)

    response = await client.patch("/users/me", json={"email": "new@x.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "new@x.com"
