"""Use case: ListUsers (US5). Admin-only, paginated."""

from __future__ import annotations

from user_api.domain.entities.user import User
from user_api.domain.exceptions import Forbidden
from user_api.domain.ports.user_repository import Page, UserRepository

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


class ListUsers:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, requester: User, page: int, page_size: int) -> Page:
        if not requester.is_admin:
            raise Forbidden("Only admins can list users.")

        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        return await self._repo.list_paginated(normalized_page, normalized_page_size)
