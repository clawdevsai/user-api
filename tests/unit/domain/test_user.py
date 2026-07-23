"""Unit tests for the User aggregate root — no infra, no fakes needed."""

from __future__ import annotations

from datetime import UTC, datetime

from user_api.domain.entities.user import Role, User, UserStatus
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


def _make_user(status: UserStatus = UserStatus.ACTIVE) -> User:
    user = User.register(Email("a@x.com"), PasswordHash("hashed"), NOW)
    user.status = status
    return user


def test_register_creates_active_user_with_default_role():
    user = User.register(Email("a@x.com"), PasswordHash("hashed"), NOW)

    assert user.status is UserStatus.ACTIVE
    assert user.roles == frozenset({Role.USER})
    assert user.created_at == NOW
    assert user.updated_at == NOW


def test_deactivate_transitions_active_to_inactive():
    user = _make_user(UserStatus.ACTIVE)
    later = datetime(2026, 7, 23, tzinfo=UTC)

    user.deactivate(later)

    assert user.status is UserStatus.INACTIVE
    assert user.updated_at == later


def test_deactivate_is_idempotent():
    user = _make_user(UserStatus.INACTIVE)
    original_updated_at = user.updated_at
    later = datetime(2026, 7, 23, tzinfo=UTC)

    user.deactivate(later)

    assert user.status is UserStatus.INACTIVE
    assert user.updated_at == original_updated_at  # no-op, timestamp untouched


def test_update_profile_changes_email_and_updated_at():
    user = _make_user()
    later = datetime(2026, 7, 24, tzinfo=UTC)

    user.update_profile(email=Email("b@x.com"), now=later)

    assert str(user.email) == "b@x.com"
    assert user.updated_at == later


def test_is_admin_reflects_roles():
    user = _make_user()
    assert user.is_admin is False

    admin_user = User(
        id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        status=UserStatus.ACTIVE,
        roles=frozenset({Role.USER, Role.ADMIN}),
        created_at=NOW,
        updated_at=NOW,
    )
    assert admin_user.is_admin is True
