"""Use case: DeactivateUser (US4). Idempotent soft-delete."""

from __future__ import annotations

from user_api.domain.entities.user import User
from user_api.domain.exceptions import Forbidden, UserNotFound
from user_api.domain.ports.clock import Clock
from user_api.domain.ports.security_audit_logger import SecurityAuditLogger
from user_api.domain.ports.user_repository import UserRepository
from user_api.domain.value_objects.user_id import UserId


class DeactivateUser:
    def __init__(
        self,
        repo: UserRepository,
        clock: Clock,
        audit_logger: SecurityAuditLogger,
    ) -> None:
        self._repo = repo
        self._clock = clock
        self._audit_logger = audit_logger

    async def execute(self, requester: User, target_id: UserId) -> None:
        if requester.id != target_id and not requester.is_admin:
            raise Forbidden("Cannot deactivate another user's account.")

        user = await self._repo.get_by_id(target_id)
        if user is None:
            raise UserNotFound(f"No user with id {target_id}")

        user.deactivate(self._clock.now())
        await self._repo.save(user)

        self._audit_logger.log_event(
            event_type="user_deactivated",
            user_id=str(user.id),
            metadata={"deactivated_by": str(requester.id)},
        )
