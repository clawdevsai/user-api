"""User-facing endpoints: register, profile, deactivate, list (admin)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from user_api.adapters.inbound.http.deps import (
    get_current_user,
    get_deactivate_user_use_case,
    get_get_user_by_id_use_case,
    get_list_users_use_case,
    get_register_user_use_case,
    get_update_user_profile_use_case,
)
from user_api.adapters.inbound.http.schemas.user_schemas import (
    RegisterUserRequest,
    UpdateProfileRequest,
    UserListResponse,
    UserResponse,
)
from user_api.application.use_cases.deactivate_user import DeactivateUser
from user_api.application.use_cases.get_user_by_id import GetUserById
from user_api.application.use_cases.list_users import ListUsers
from user_api.application.use_cases.register_user import RegisterUser
from user_api.application.use_cases.update_user_profile import UpdateUserProfile
from user_api.domain.entities.user import User
from user_api.domain.exceptions import (
    EmailAlreadyRegistered,
    Forbidden,
    InvalidEmail,
    UserNotFound,
    WeakPassword,
)
from user_api.domain.value_objects.user_id import UserId

router = APIRouter(tags=["users"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterUserRequest,
    use_case: RegisterUser = Depends(get_register_user_use_case),
) -> UserResponse:
    try:
        user = await use_case.execute(payload.email, payload.password)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="EMAIL_ALREADY_REGISTERED") from exc
    except (InvalidEmail, WeakPassword) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return UserResponse.from_domain(user)


@router.get("/users/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    use_case: GetUserById = Depends(get_get_user_by_id_use_case),
) -> UserResponse:
    user = await use_case.execute(current_user, current_user.id)
    return UserResponse.from_domain(user)


@router.patch("/users/me", response_model=UserResponse)
async def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateUserProfile = Depends(get_update_user_profile_use_case),
) -> UserResponse:
    try:
        user = await use_case.execute(current_user, current_user.id, email=payload.email)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="EMAIL_ALREADY_REGISTERED") from exc
    except InvalidEmail as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return UserResponse.from_domain(user)


@router.post("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    use_case: DeactivateUser = Depends(get_deactivate_user_use_case),
) -> None:
    try:
        await use_case.execute(current_user, UserId(user_id))
    except Forbidden as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except UserNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    use_case: ListUsers = Depends(get_list_users_use_case),
) -> UserListResponse:
    try:
        result = await use_case.execute(current_user, page, page_size)
    except Forbidden as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return UserListResponse(
        items=[UserResponse.from_domain(u) for u in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )
