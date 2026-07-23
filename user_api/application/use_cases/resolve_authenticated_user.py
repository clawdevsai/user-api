"""Use case: ResolveAuthenticatedUser — resolves identity from already-validated JWT claims.

Used by the HTTP `get_current_user` dependency. Rejects inactive users on
every request (FR-011), even if the JWT itself is still technically valid.
"""

from __future__ import annotations

import uuid

from user_api.domain.entities.user import User, UserStatus
from user_api.domain.exceptions import UserInactive, UserNotFound
from user_api.domain.ports.user_repository import UserRepository
from user_api.domain.value_objects.user_id import UserId


class ResolveAuthenticatedUser:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> User:
        user = await self._repo.get_by_id(UserId(uuid.UUID(user_id)))
        if user is None:
            raise UserNotFound(f"No user with id {user_id}")
        if user.status is not UserStatus.ACTIVE:
            raise UserInactive(f"User {user_id} is inactive.")
        return user
