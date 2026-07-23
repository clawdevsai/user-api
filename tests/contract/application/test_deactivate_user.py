"""Contract tests for DeactivateUser (authorization + idempotency)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.unit.fakes import FakeClock, FakeSecurityAuditLogger, FakeUserRepository
from user_api.application.use_cases.deactivate_user import DeactivateUser
from user_api.domain.entities.user import Role, User, UserStatus
from user_api.domain.exceptions import Forbidden
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash

NOW = datetime(2026, 7, 22, tzinfo=UTC)


def _make_user(email: str, roles: frozenset[Role] = frozenset({Role.USER})) -> User:
    user = User.register(Email(email), PasswordHash("hashed"), NOW)
    user.roles = roles
    return user


async def test_deactivate_user_owner_can_deactivate_self():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    await repo.save(owner)
    use_case = DeactivateUser(repo, FakeClock(NOW), FakeSecurityAuditLogger())

    await use_case.execute(owner, owner.id)

    stored = await repo.get_by_id(owner.id)
    assert stored is not None
    assert stored.status is UserStatus.INACTIVE


async def test_deactivate_user_is_idempotent():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    await repo.save(owner)
    use_case = DeactivateUser(repo, FakeClock(NOW), FakeSecurityAuditLogger())

    await use_case.execute(owner, owner.id)
    await use_case.execute(owner, owner.id)  # second call must not raise

    stored = await repo.get_by_id(owner.id)
    assert stored is not None
    assert stored.status is UserStatus.INACTIVE


async def test_deactivate_user_non_owner_non_admin_forbidden():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    stranger = _make_user("stranger@x.com")
    await repo.save(owner)
    await repo.save(stranger)
    use_case = DeactivateUser(repo, FakeClock(NOW), FakeSecurityAuditLogger())

    with pytest.raises(Forbidden):
        await use_case.execute(stranger, owner.id)


async def test_deactivate_user_admin_can_deactivate_others():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    admin = _make_user("admin@x.com", roles=frozenset({Role.USER, Role.ADMIN}))
    await repo.save(owner)
    await repo.save(admin)
    use_case = DeactivateUser(repo, FakeClock(NOW), FakeSecurityAuditLogger())

    await use_case.execute(admin, owner.id)

    stored = await repo.get_by_id(owner.id)
    assert stored is not None
    assert stored.status is UserStatus.INACTIVE
