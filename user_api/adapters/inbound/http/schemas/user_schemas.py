"""Pydantic request/response schemas for user endpoints. Never includes password_hash."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from user_api.domain.entities.user import User


class RegisterUserRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    email: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    status: str
    roles: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, user: User) -> UserResponse:
        return cls(
            id=user.id.value,
            email=str(user.email),
            status=user.status.value,
            roles=sorted(r.value for r in user.roles),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class UserListResponse(BaseModel):
    items: list[UserResponse]
    page: int
    page_size: int
    total: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
