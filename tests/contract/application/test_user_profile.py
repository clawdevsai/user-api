"""Contract tests for GetUserById and UpdateUserProfile (owner/admin authorization)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.unit.fakes import FakeClock, FakeUserRepository
from user_api.application.use_cases.get_user_by_id import GetUserById
from user_api.application.use_cases.update_user_profile import UpdateUserProfile
from user_api.domain.entities.user import Role, User
from user_api.domain.exceptions import EmailAlreadyRegistered, Forbidden
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash

NOW = datetime(2026, 7, 22, tzinfo=UTC)


def _make_user(email: str, roles: frozenset[Role] = frozenset({Role.USER})) -> User:
    user = User.register(Email(email), PasswordHash("hashed"), NOW)
    user.roles = roles
    return user


async def test_get_user_by_id_owner_can_view_self():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    await repo.save(owner)
    use_case = GetUserById(repo)

    result = await use_case.execute(owner, owner.id)

    assert result.id == owner.id


async def test_get_user_by_id_non_owner_non_admin_forbidden():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    stranger = _make_user("stranger@x.com")
    await repo.save(owner)
    await repo.save(stranger)
    use_case = GetUserById(repo)

    with pytest.raises(Forbidden):
        await use_case.execute(stranger, owner.id)


async def test_get_user_by_id_admin_can_view_others():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    admin = _make_user("admin@x.com", roles=frozenset({Role.USER, Role.ADMIN}))
    await repo.save(owner)
    await repo.save(admin)
    use_case = GetUserById(repo)

    result = await use_case.execute(admin, owner.id)

    assert result.id == owner.id


async def test_update_user_profile_owner_can_update_email():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    await repo.save(owner)
    use_case = UpdateUserProfile(repo, FakeClock(NOW))

    updated = await use_case.execute(owner, owner.id, email="new@x.com")

    assert str(updated.email) == "new@x.com"


async def test_update_user_profile_rejects_email_in_use():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    other = _make_user("other@x.com")
    await repo.save(owner)
    await repo.save(other)
    use_case = UpdateUserProfile(repo, FakeClock(NOW))

    with pytest.raises(EmailAlreadyRegistered):
        await use_case.execute(owner, owner.id, email="other@x.com")


async def test_update_user_profile_non_owner_non_admin_forbidden():
    repo = FakeUserRepository()
    owner = _make_user("owner@x.com")
    stranger = _make_user("stranger@x.com")
    await repo.save(owner)
    await repo.save(stranger)
    use_case = UpdateUserProfile(repo, FakeClock(NOW))

    with pytest.raises(Forbidden):
        await use_case.execute(stranger, owner.id, email="hacked@x.com")
