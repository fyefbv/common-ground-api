from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user_email, get_user_service
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

users_router = APIRouter(prefix="/users", tags=["Пользователи"])


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_email),
) -> UserResponse:
    return await user_service.get_user(user_id)


@users_router.get("/", response_model=list[UserResponse])
async def get_users(
    user_service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_email),
) -> list[UserResponse]:
    return await user_service.get_users()


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_email),
) -> UserResponse:
    return await user_service.update_user(user_id, user_update)


@users_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_email),
) -> dict:
    await user_service.delete_user(user_id)
    return {"detail": "User deleted successfully"}
