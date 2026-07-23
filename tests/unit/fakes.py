"""Deterministic test doubles for domain Ports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from user_api.domain.entities.user import User
from user_api.domain.exceptions import EmailAlreadyRegistered
from user_api.domain.ports.user_repository import Page
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.user_id import UserId


class FakeClock:
    def __init__(self, fixed_now: datetime) -> None:
        self._fixed_now = fixed_now

    def now(self) -> datetime:
        return self._fixed_now

    def advance(self, new_now: datetime) -> None:
        self._fixed_now = new_now


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    async def save(self, user: User) -> None:
        existing = await self.get_by_email(user.email)
        if existing is not None and existing.id != user.id:
            raise EmailAlreadyRegistered(f"Email already registered: {user.email}")
        self.users[str(user.id)] = user

    async def get_by_id(self, user_id: UserId) -> User | None:
        return self.users.get(str(user_id))

    async def get_by_email(self, email: Email) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def list_paginated(self, page: int, page_size: int) -> Page:
        all_users = sorted(self.users.values(), key=lambda u: u.created_at)
        start = (page - 1) * page_size
        end = start + page_size
        return Page(
            items=all_users[start:end],
            page=page,
            page_size=page_size,
            total=len(all_users),
        )


class FakePasswordHasher:
    """Deterministic fake: 'hashed:<plain>'. Never use outside tests."""

    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{plain_password}"


class FakeSecurityAuditLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str | None, dict[str, Any]]] = []

    def log_event(self, event_type: str, user_id: str | None, metadata: dict[str, Any]) -> None:
        self.events.append((event_type, user_id, metadata))
