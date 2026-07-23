"""Password (plaintext, transient) and PasswordHash (persisted) value objects.

`Password` never persists, never logs, never serializes: it exists only for
the duration of `RegisterUser` / `VerifyCredentials` use cases.
"""

from __future__ import annotations

from dataclasses import dataclass

from user_api.domain.exceptions import WeakPassword

_MIN_LENGTH = 8
_COMMON_PASSWORDS = frozenset(
    {
        "password",
        "12345678",
        "123456789",
        "qwerty123",
        "senha123",
        "password1",
        "letmein11",
    }
)


@dataclass(frozen=True, slots=True)
class Password:
    """Plaintext password. Validated against a minimal complexity policy."""

    plain_text: str

    def __post_init__(self) -> None:
        if len(self.plain_text) < _MIN_LENGTH:
            raise WeakPassword(f"Password must have at least {_MIN_LENGTH} characters.")
        if self.plain_text.lower() in _COMMON_PASSWORDS:
            raise WeakPassword("Password is too common.")

    def __repr__(self) -> str:
        return "Password(***)"


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Opaque hash produced by a `PasswordHasher` port adapter (e.g. Argon2id)."""

    value: str

    def __repr__(self) -> str:
        return "PasswordHash(***)"
