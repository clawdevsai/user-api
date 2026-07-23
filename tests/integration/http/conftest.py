"""Shared fixtures for HTTP integration tests.

Requires a real, reachable Postgres (DATABASE_URL env var, defaults to
localhost). Tests in this package are skipped automatically if no Postgres
is reachable — see quickstart.md for the manual validation this substitutes
in CI/local environments with Docker available.

ponytail: auth is exercised via a dependency override (`get_current_user`)
rather than real signed JWTs / a live JWKS server — this keeps focus on the
request/response contract and persistence, not JWT crypto (already covered
by pyjwt itself). Add a real JWKS-backed test if this proves insufficient.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

os.environ.setdefault("JWKS_URL", "https://idp.example.com/.well-known/jwks.json")
os.environ.setdefault("JWT_ISSUER", "https://idp.example.com/")
os.environ.setdefault("JWT_AUDIENCE", "user-api")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://user_api:user_api@localhost:5432/user_api_test",
)

from user_api.adapters.inbound.http import deps  # noqa: E402
from user_api.adapters.inbound.http.main import app  # noqa: E402
from user_api.adapters.outbound.persistence.models import Base  # noqa: E402
from user_api.adapters.outbound.persistence.session import (  # noqa: E402
    make_engine,
    make_session_factory,
)
from user_api.adapters.outbound.persistence.user_repository_sqlalchemy import (  # noqa: E402
    SQLAlchemyUserRepository,
)
from user_api.domain.entities.user import Role, User, UserStatus  # noqa: E402
from user_api.domain.value_objects.email import Email  # noqa: E402
from user_api.domain.value_objects.password import PasswordHash  # noqa: E402


async def _postgres_reachable() -> bool:
    try:
        engine = make_engine()
        async with engine.connect():
            pass
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _require_postgres() -> None:
    if not await _postgres_reachable():
        pytest.skip("Postgres not reachable at DATABASE_URL — skipping HTTP integration tests.")


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = make_session_factory(engine)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override_get_user_repository() -> AsyncIterator[SQLAlchemyUserRepository]:
        yield SQLAlchemyUserRepository(db_session)

    app.dependency_overrides[deps.get_user_repository] = _override_get_user_repository
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def make_authenticated_override(user: User):
    async def _override() -> User:
        return user

    return _override


async def create_user(
    session: AsyncSession,
    email: str,
    plain_password: str,
    *,
    roles: frozenset[Role] = frozenset({Role.USER}),
    status_: UserStatus = UserStatus.ACTIVE,
) -> User:
    from datetime import UTC, datetime

    from user_api.adapters.outbound.security.argon2_password_hasher import Argon2PasswordHasher

    repo = SQLAlchemyUserRepository(session)
    hasher = Argon2PasswordHasher()
    user = User.register(Email(email), PasswordHash(hasher.hash(plain_password)), datetime.now(UTC))
    user.roles = roles
    if status_ is UserStatus.INACTIVE:
        user.deactivate(datetime.now(UTC))
    await repo.save(user)
    return user


def as_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)
