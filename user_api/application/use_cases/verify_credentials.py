"""Use case: VerifyCredentials (US2) — internal port consumed only by the external IdP.

Returns identical failure behavior for "user does not exist", "wrong password",
and "inactive user" (FR-016): always raises InvalidCredentials, never leaking
which case occurred. Always performs a hash comparison (real or dummy) to
avoid leaking existence via response timing.
"""

from __future__ import annotations

from dataclasses import dataclass

from user_api.domain.entities.user import Role, UserStatus
from user_api.domain.exceptions import InvalidCredentials
from user_api.domain.ports.password_hasher import PasswordHasher
from user_api.domain.ports.security_audit_logger import SecurityAuditLogger
from user_api.domain.ports.user_repository import UserRepository
from user_api.domain.value_objects.email import Email


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    id: str
    roles: frozenset[Role]
    status: UserStatus


class VerifyCredentials:
    def __init__(
        self,
        repo: UserRepository,
        hasher: PasswordHasher,
        audit_logger: SecurityAuditLogger,
        dummy_hash: str,
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._audit_logger = audit_logger
        self._dummy_hash = dummy_hash

    async def execute(self, email: str, password: str) -> VerifiedIdentity:
        validated_email = Email(email)
        user = await self._repo.get_by_email(validated_email)

        # Always verify against a hash (real or dummy) to keep timing constant
        # regardless of whether the user exists (FR-016).
        hash_to_check = user.password_hash.value if user is not None else self._dummy_hash
        password_matches = self._hasher.verify(password, hash_to_check)

        if user is None or not password_matches or user.status is not UserStatus.ACTIVE:
            self._audit_logger.log_event(
                event_type="credential_verification_failed",
                user_id=str(user.id) if user is not None else None,
                metadata={},
            )
            raise InvalidCredentials("Invalid email or password.")

        self._audit_logger.log_event(
            event_type="credential_verification_succeeded",
            user_id=str(user.id),
            metadata={},
        )
        return VerifiedIdentity(id=str(user.id), roles=user.roles, status=user.status)
