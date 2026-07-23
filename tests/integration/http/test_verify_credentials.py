"""Integration test: quickstart.md scenario 2 + inactive-user rejection (FR-011)."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.http.conftest import create_user
from user_api.domain.entities.user import UserStatus

INTERNAL_HEADERS = {"X-Internal-Api-Key": "test-internal-key"}


async def test_verify_credentials_success(client: AsyncClient, db_session: AsyncSession):
    await create_user(db_session, "a@x.com", "Senha123!")

    response = await client.post(
        "/internal/credentials/verify",
        json={"email": "a@x.com", "password": "Senha123!"},
        headers=INTERNAL_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert "password" not in body
    assert body["status"] == "ACTIVE"


async def test_verify_credentials_wrong_password_401(client: AsyncClient, db_session: AsyncSession):
    await create_user(db_session, "a@x.com", "Senha123!")

    response = await client.post(
        "/internal/credentials/verify",
        json={"email": "a@x.com", "password": "wrong-pass"},
        headers=INTERNAL_HEADERS,
    )

    assert response.status_code == 401


async def test_verify_credentials_inactive_user_401(client: AsyncClient, db_session: AsyncSession):
    await create_user(db_session, "a@x.com", "Senha123!", status_=UserStatus.INACTIVE)

    response = await client.post(
        "/internal/credentials/verify",
        json={"email": "a@x.com", "password": "Senha123!"},
        headers=INTERNAL_HEADERS,
    )

    assert response.status_code == 401


async def test_verify_credentials_unauthorized_caller_403(client: AsyncClient):
    response = await client.post(
        "/internal/credentials/verify",
        json={"email": "a@x.com", "password": "Senha123!"},
        headers={"X-Internal-Api-Key": "wrong-key"},
    )

    assert response.status_code == 403
