"""Use case: UpdateUserProfile (US3).

v1 scope: only `email` is updatable. Password and roles are out of scope
(spec Assumptions). Caller must be the owner or an admin.
"""

from __future__ import annotations

from user_api.domain.entities.user import User
from user_api.domain.exceptions import EmailAlreadyRegistered, Forbidden, UserNotFound
from user_api.domain.ports.clock import Clock
from user_api.domain.ports.user_repository import UserRepository
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.user_id import UserId


class UpdateUserProfile:
    def __init__(self, repo: UserRepository, clock: Clock) -> None:
        self._repo = repo
        self._clock = clock

    async def execute(self, requester: User, target_id: UserId, *, email: str | None) -> User:
        if requester.id != target_id and not requester.is_admin:
            raise Forbidden("Cannot update another user's profile.")

        user = await self._repo.get_by_id(target_id)
        if user is None:
            raise UserNotFound(f"No user with id {target_id}")

        new_email = Email(email) if email is not None else None
        if new_email is not None and new_email != user.email:
            existing = await self._repo.get_by_email(new_email)
            if existing is not None and existing.id != user.id:
                raise EmailAlreadyRegistered(f"Email already in use: {new_email}")

        user.update_profile(email=new_email, now=self._clock.now())
        await self._repo.save(user)
        return user
