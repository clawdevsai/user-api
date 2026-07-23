"""Dependency injection: Ports -> Adapters wiring, and auth dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from user_api.adapters.outbound.observability.clock import SystemClock
from user_api.adapters.outbound.observability.structured_logger import StructuredSecurityAuditLogger
from user_api.adapters.outbound.persistence.session import get_session
from user_api.adapters.outbound.persistence.user_repository_sqlalchemy import (
    SQLAlchemyUserRepository,
)
from user_api.adapters.outbound.security.argon2_password_hasher import (
    DUMMY_HASH,
    Argon2PasswordHasher,
)
from user_api.adapters.outbound.security.jwt_validator import InvalidToken, JwtValidator
from user_api.application.use_cases.deactivate_user import DeactivateUser
from user_api.application.use_cases.get_user_by_id import GetUserById
from user_api.application.use_cases.list_users import ListUsers
from user_api.application.use_cases.register_user import RegisterUser
from user_api.application.use_cases.resolve_authenticated_user import ResolveAuthenticatedUser
from user_api.application.use_cases.update_user_profile import UpdateUserProfile
from user_api.application.use_cases.verify_credentials import VerifyCredentials
from user_api.config import Settings, get_settings
from user_api.domain.entities.user import User
from user_api.domain.exceptions import UserInactive, UserNotFound


def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def _jwt_validator(jwks_url: str, issuer: str, audience: str) -> JwtValidator:
    return JwtValidator(jwks_url=jwks_url, issuer=issuer, audience=audience)


def get_jwt_validator(settings: Settings = Depends(get_app_settings)) -> JwtValidator:
    return _jwt_validator(settings.jwks_url, settings.jwt_issuer, settings.jwt_audience)


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SQLAlchemyUserRepository]:
    yield SQLAlchemyUserRepository(session)


def get_clock() -> SystemClock:
    return SystemClock()


def get_password_hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher()


def get_audit_logger() -> StructuredSecurityAuditLogger:
    return StructuredSecurityAuditLogger()


def get_register_user_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    hasher: Argon2PasswordHasher = Depends(get_password_hasher),
    clock: SystemClock = Depends(get_clock),
    audit_logger: StructuredSecurityAuditLogger = Depends(get_audit_logger),
) -> RegisterUser:
    return RegisterUser(repo, hasher, clock, audit_logger)


def get_verify_credentials_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    hasher: Argon2PasswordHasher = Depends(get_password_hasher),
    audit_logger: StructuredSecurityAuditLogger = Depends(get_audit_logger),
) -> VerifyCredentials:
    return VerifyCredentials(repo, hasher, audit_logger, dummy_hash=DUMMY_HASH)


def get_resolve_authenticated_user_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> ResolveAuthenticatedUser:
    return ResolveAuthenticatedUser(repo)


def get_get_user_by_id_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> GetUserById:
    return GetUserById(repo)


def get_update_user_profile_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    clock: SystemClock = Depends(get_clock),
) -> UpdateUserProfile:
    return UpdateUserProfile(repo, clock)


def get_deactivate_user_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    clock: SystemClock = Depends(get_clock),
    audit_logger: StructuredSecurityAuditLogger = Depends(get_audit_logger),
) -> DeactivateUser:
    return DeactivateUser(repo, clock, audit_logger)


def get_list_users_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> ListUsers:
    return ListUsers(repo)


async def get_current_user(
    authorization: str | None = Header(default=None),
    jwt_validator: JwtValidator = Depends(get_jwt_validator),
    resolve_use_case: ResolveAuthenticatedUser = Depends(get_resolve_authenticated_user_use_case),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Missing or malformed bearer token."
        )
    token = authorization.removeprefix("Bearer ").strip()

    try:
        claims = jwt_validator.validate(token)
    except InvalidToken as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token."
        ) from exc

    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token missing subject claim.")

    try:
        return await resolve_use_case.execute(subject)
    except UserNotFound as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token."
        ) from exc
    except UserInactive as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="User is inactive.") from exc


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_app_settings),
) -> None:
    if x_internal_api_key is None or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Unauthorized internal caller.")
