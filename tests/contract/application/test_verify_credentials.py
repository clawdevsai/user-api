"""Contract tests for VerifyCredentials — indistinguishable failure response (FR-016)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.unit.fakes import FakePasswordHasher, FakeSecurityAuditLogger, FakeUserRepository
from user_api.application.use_cases.verify_credentials import VerifyCredentials
from user_api.domain.entities.user import User
from user_api.domain.exceptions import InvalidCredentials
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash

NOW = datetime(2026, 7, 22, tzinfo=UTC)


async def _repo_with_user(hasher: FakePasswordHasher, active: bool = True) -> FakeUserRepository:
    repo = FakeUserRepository()
    user = User.register(Email("test@example.com"), PasswordHash(hasher.hash("Senha123!")), NOW)
    if not active:
        user.deactivate(NOW)
    await repo.save(user)
    return repo


async def test_verify_credentials_success():
    hasher = FakePasswordHasher()
    repo = await _repo_with_user(hasher)
    use_case = VerifyCredentials(repo, hasher, FakeSecurityAuditLogger(), dummy_hash="hashed:dummy")

    identity = await use_case.execute("test@example.com", "Senha123!")

    assert identity.id
    assert identity.status.value == "ACTIVE"


async def test_verify_credentials_rejects_wrong_password():
    hasher = FakePasswordHasher()
    repo = await _repo_with_user(hasher)
    use_case = VerifyCredentials(repo, hasher, FakeSecurityAuditLogger(), dummy_hash="hashed:dummy")

    with pytest.raises(InvalidCredentials):
        await use_case.execute("test@example.com", "wrong-password")


async def test_verify_credentials_rejects_nonexistent_user():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    use_case = VerifyCredentials(repo, hasher, FakeSecurityAuditLogger(), dummy_hash="hashed:dummy")

    with pytest.raises(InvalidCredentials):
        await use_case.execute("nobody@example.com", "whatever1")


async def test_verify_credentials_rejects_inactive_user_even_with_correct_password():
    hasher = FakePasswordHasher()
    repo = await _repo_with_user(hasher, active=False)
    use_case = VerifyCredentials(repo, hasher, FakeSecurityAuditLogger(), dummy_hash="hashed:dummy")

    with pytest.raises(InvalidCredentials):
        await use_case.execute("test@example.com", "Senha123!")
