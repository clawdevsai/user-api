"""Argon2id password hasher adapter (implements PasswordHasher port)."""

from __future__ import annotations

from argon2 import PasswordHasher as Argon2Impl
from argon2.exceptions import VerifyMismatchError

_argon2 = Argon2Impl()

# Precomputed hash of a random value, used to burn equivalent CPU time when
# verifying against a non-existent user (FR-016 timing-attack mitigation).
DUMMY_HASH = _argon2.hash("dummy-password-for-timing-parity")


class Argon2PasswordHasher:
    def hash(self, plain_password: str) -> str:
        return _argon2.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        try:
            return _argon2.verify(password_hash, plain_password)
        except VerifyMismatchError:
            return False
