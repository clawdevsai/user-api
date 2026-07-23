"""Use case: RegisterUser (US1)."""

from __future__ import annotations

from user_api.domain.entities.user import User
from user_api.domain.exceptions import EmailAlreadyRegistered
from user_api.domain.ports.clock import Clock
from user_api.domain.ports.password_hasher import PasswordHasher
from user_api.domain.ports.security_audit_logger import SecurityAuditLogger
from user_api.domain.ports.user_repository import UserRepository
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import Password, PasswordHash


class RegisterUser:
    def __init__(
        self,
        repo: UserRepository,
        hasher: PasswordHasher,
        clock: Clock,
        audit_logger: SecurityAuditLogger,
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._clock = clock
        self._audit_logger = audit_logger

    async def execute(self, email: str, password: str) -> User:
        validated_email = Email(email)
        validated_password = Password(password)  # raises WeakPassword if policy violated

        if await self._repo.get_by_email(validated_email) is not None:
            raise EmailAlreadyRegistered(f"Email already registered: {validated_email}")

        password_hash = PasswordHash(self._hasher.hash(validated_password.plain_text))
        user = User.register(validated_email, password_hash, self._clock.now())
        await self._repo.save(user)

        self._audit_logger.log_event(
            event_type="user_registered",
            user_id=str(user.id),
            metadata={"email": str(user.email)},
        )
        return user
