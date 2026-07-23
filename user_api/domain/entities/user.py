"""User aggregate root. No FastAPI/SQLAlchemy/PyJWT/argon2 imports here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from user_api.domain.ports.password_hasher import PasswordHasher
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash
from user_api.domain.value_objects.user_id import UserId


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Role(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


# Profile fields that MAY be changed via UpdateUserProfile (v1 scope).
# Password and roles are explicitly out of scope for profile updates (spec Assumptions).
UPDATABLE_PROFILE_FIELDS = frozenset({"email"})


@dataclass
class User:
    id: UserId
    email: Email
    password_hash: PasswordHash
    status: UserStatus
    roles: frozenset[Role]
    created_at: datetime
    updated_at: datetime = field(compare=False)

    @classmethod
    def register(cls, email: Email, password_hash: PasswordHash, now: datetime) -> User:
        return cls(
            id=UserId.new(),
            email=email,
            password_hash=password_hash,
            status=UserStatus.ACTIVE,
            roles=frozenset({Role.USER}),
            created_at=now,
            updated_at=now,
        )

    def deactivate(self, now: datetime) -> None:
        """Idempotent: deactivating an already-inactive user is a no-op."""
        if self.status is UserStatus.INACTIVE:
            return
        self.status = UserStatus.INACTIVE
        self.updated_at = now

    def update_profile(self, *, email: Email | None, now: datetime) -> None:
        if email is not None:
            self.email = email
        self.updated_at = now

    def verify_password(self, plain_password: str, hasher: PasswordHasher) -> bool:
        """Delegates to the PasswordHasher port; never compares strings directly.

        Does NOT check `status` — callers (use cases) are responsible for
        rejecting inactive users (FR-011), since the exact error mapping
        differs per use case (e.g. indistinguishable response, FR-016).
        """
        return hasher.verify(plain_password, self.password_hash.value)

    @property
    def is_admin(self) -> bool:
        return Role.ADMIN in self.roles
