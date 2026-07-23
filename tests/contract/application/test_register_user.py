"""Contract tests for RegisterUser use case, using fakes for all Ports."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.unit.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeSecurityAuditLogger,
    FakeUserRepository,
)
from user_api.application.use_cases.register_user import RegisterUser
from user_api.domain.exceptions import EmailAlreadyRegistered, WeakPassword


def _make_use_case() -> tuple[RegisterUser, FakeUserRepository, FakeSecurityAuditLogger]:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    clock = FakeClock(datetime(2026, 7, 22, tzinfo=UTC))
    audit_logger = FakeSecurityAuditLogger()
    return RegisterUser(repo, hasher, clock, audit_logger), repo, audit_logger


async def test_register_user_success():
    use_case, repo, audit_logger = _make_use_case()

    user = await use_case.execute("test@example.com", "Senha123!")

    assert str(user.email) == "test@example.com"
    assert len(repo.users) == 1
    assert audit_logger.events[0][0] == "user_registered"


async def test_register_user_rejects_duplicate_email():
    use_case, _repo, _audit_logger = _make_use_case()
    await use_case.execute("test@example.com", "Senha123!")

    with pytest.raises(EmailAlreadyRegistered):
        await use_case.execute("test@example.com", "OutraSenha1!")


async def test_register_user_rejects_weak_password():
    use_case, _repo, _audit_logger = _make_use_case()

    with pytest.raises(WeakPassword):
        await use_case.execute("test@example.com", "1234567")
