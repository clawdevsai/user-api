"""Integration test: quickstart.md scenario 4 (deactivation, idempotent + FR-011)."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.http.conftest import create_user, make_authenticated_override
from user_api.adapters.inbound.http import deps
from user_api.adapters.inbound.http.main import app

INTERNAL_HEADERS = {"X-Internal-Api-Key": "test-internal-key"}


async def test_deactivate_then_credentials_rejected_then_idempotent(
    client: AsyncClient, db_session: AsyncSession
):
    user = await create_user(db_session, "a@x.com", "Senha123!")
    app.dependency_overrides[deps.get_current_user] = make_authenticated_override(user)

    first = await client.post(f"/users/{user.id}/deactivate")
    assert first.status_code == 204

    verify = await client.post(
        "/internal/credentials/verify",
        json={"email": "a@x.com", "password": "Senha123!"},
        headers=INTERNAL_HEADERS,
    )
    assert verify.status_code == 401

    second = await client.post(f"/users/{user.id}/deactivate")
    assert second.status_code == 204


async def test_deactivate_forbidden_for_non_owner_non_admin(
    client: AsyncClient, db_session: AsyncSession
):
    owner = await create_user(db_session, "owner@x.com", "Senha123!")
    stranger = await create_user(db_session, "stranger@x.com", "Senha123!")
    app.dependency_overrides[deps.get_current_user] = make_authenticated_override(stranger)

    response = await client.post(f"/users/{owner.id}/deactivate")

    assert response.status_code == 403
