"""Contract tests for ResolveAuthenticatedUser."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.unit.fakes import FakeUserRepository
from user_api.application.use_cases.resolve_authenticated_user import ResolveAuthenticatedUser
from user_api.domain.entities.user import User
from user_api.domain.exceptions import UserInactive, UserNotFound
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash

NOW = datetime(2026, 7, 22, tzinfo=UTC)


async def test_resolve_authenticated_user_active_resolves():
    repo = FakeUserRepository()
    user = User.register(Email("a@x.com"), PasswordHash("hashed"), NOW)
    await repo.save(user)
    use_case = ResolveAuthenticatedUser(repo)

    resolved = await use_case.execute(str(user.id))

    assert resolved.id == user.id


async def test_resolve_authenticated_user_inactive_raises():
    repo = FakeUserRepository()
    user = User.register(Email("a@x.com"), PasswordHash("hashed"), NOW)
    user.deactivate(NOW)
    await repo.save(user)
    use_case = ResolveAuthenticatedUser(repo)

    with pytest.raises(UserInactive):
        await use_case.execute(str(user.id))


async def test_resolve_authenticated_user_not_found_raises():
    repo = FakeUserRepository()
    use_case = ResolveAuthenticatedUser(repo)

    with pytest.raises(UserNotFound):
        await use_case.execute("00000000-0000-0000-0000-000000000000")
