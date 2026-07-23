"""SQLAlchemy implementation of the UserRepository port."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from user_api.adapters.outbound.persistence.models import UserModel
from user_api.domain.entities.user import Role, User, UserStatus
from user_api.domain.exceptions import EmailAlreadyRegistered
from user_api.domain.ports.user_repository import Page
from user_api.domain.value_objects.email import Email
from user_api.domain.value_objects.password import PasswordHash
from user_api.domain.value_objects.user_id import UserId


def _to_domain(model: UserModel) -> User:
    return User(
        id=UserId(model.id),
        email=Email(model.email),
        password_hash=PasswordHash(model.password_hash),
        status=UserStatus(model.status),
        roles=frozenset(Role(r) for r in model.roles),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id.value,
        email=user.email.value,
        password_hash=user.password_hash.value,
        status=user.status.value,
        roles=[r.value for r in user.roles],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id.value)
        if model is None:
            model = _to_model(user)
            self._session.add(model)
        else:
            model.email = user.email.value
            model.password_hash = user.password_hash.value
            model.status = user.status.value
            model.roles = [r.value for r in user.roles]
            model.updated_at = user.updated_at
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyRegistered(f"Email already registered: {user.email}") from exc

    async def get_by_id(self, user_id: UserId) -> User | None:
        model = await self._session.get(UserModel, user_id.value)
        return _to_domain(model) if model is not None else None

    async def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(func.lower(UserModel.email) == email.value)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def list_paginated(self, page: int, page_size: int) -> Page:
        total = await self._session.scalar(select(func.count()).select_from(UserModel))
        stmt = (
            select(UserModel)
            .order_by(UserModel.created_at)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = [_to_domain(model) for model in result.scalars().all()]
        return Page(items=items, page=page, page_size=page_size, total=total or 0)
