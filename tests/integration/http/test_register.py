"""Integration test: quickstart.md scenario 1 (registration)."""

from __future__ import annotations

from httpx import AsyncClient


async def test_register_then_duplicate_email_conflict(client: AsyncClient):
    response = await client.post("/users", json={"email": "a@x.com", "password": "Senha123!"})
    assert response.status_code == 201
    body = response.json()
    assert "password_hash" not in body
    assert "password" not in body
    assert body["status"] == "ACTIVE"

    duplicate = await client.post("/users", json={"email": "a@x.com", "password": "Outra123!"})
    assert duplicate.status_code == 409


async def test_register_rejects_weak_password(client: AsyncClient):
    response = await client.post("/users", json={"email": "b@x.com", "password": "short"})
    assert response.status_code == 422
