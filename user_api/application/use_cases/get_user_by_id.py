"""Use case: GetUserById (US3). Caller must be the owner or an admin."""

from __future__ import annotations

from user_api.domain.entities.user import User
from user_api.domain.exceptions import Forbidden, UserNotFound
from user_api.domain.ports.user_repository import UserRepository
from user_api.domain.value_objects.user_id import UserId


class GetUserById:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, requester: User, target_id: UserId) -> User:
        if requester.id != target_id and not requester.is_admin:
            raise Forbidden("Cannot view another user's profile.")
        user = await self._repo.get_by_id(target_id)
        if user is None:
            raise UserNotFound(f"No user with id {target_id}")
        return user
