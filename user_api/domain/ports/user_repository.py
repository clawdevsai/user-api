"""Port: persistence boundary for the User aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from user_api.domain.entities.user import User
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class Page:
    items: list[User]
    page: int
    page_size: int
    total: int


class UserRepository(Protocol):
    async def save(self, user: User) -> None: ...

    async def get_by_id(self, user_id: UserId) -> User | None: ...

    async def get_by_email(self, email: Email) -> User | None: ...

    async def list_paginated(self, page: int, page_size: int) -> Page: ...
