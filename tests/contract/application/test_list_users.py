"""Contract tests for ListUsers (pagination + admin-only authorization)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.unit.fakes import FakeUserRepository
from user_api.application.use_cases.list_users import ListUsers
from user_api.domain.entities.user import Role, User
from user_api.domain.exceptions import Forbidden
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash

NOW = datetime(2026, 7, 22, tzinfo=UTC)


def _make_user(email: str, roles: frozenset[Role] = frozenset({Role.USER})) -> User:
    user = User.register(Email(email), PasswordHash("hashed"), NOW)
    user.roles = roles
    return user


async def test_list_users_admin_gets_paginated_results():
    repo = FakeUserRepository()
    admin = _make_user("admin@x.com", roles=frozenset({Role.USER, Role.ADMIN}))
    await repo.save(admin)
    for i in range(3):
        await repo.save(_make_user(f"user{i}@x.com"))
    use_case = ListUsers(repo)

    page = await use_case.execute(admin, page=1, page_size=2)

    assert page.total == 4
    assert len(page.items) == 2
    assert page.page == 1
    assert page.page_size == 2


async def test_list_users_normalizes_invalid_pagination_params():
    repo = FakeUserRepository()
    admin = _make_user("admin@x.com", roles=frozenset({Role.USER, Role.ADMIN}))
    await repo.save(admin)
    use_case = ListUsers(repo)

    page = await use_case.execute(admin, page=-1, page_size=99999)

    assert page.page == 1
    assert page.page_size == 100  # MAX_PAGE_SIZE


async def test_list_users_non_admin_forbidden():
    repo = FakeUserRepository()
    regular_user = _make_user("user@x.com")
    use_case = ListUsers(repo)

    with pytest.raises(Forbidden):
        await use_case.execute(regular_user, page=1, page_size=20)
