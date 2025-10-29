from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user, get_user_service
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

users_router = APIRouter(prefix="/users", tags=["Пользователи"])


@users_router.get("/me", response_model=UserResponse)
async def get_user(
    user_service: UserService = Depends(get_user_service),
    user: UUID = Depends(get_current_user),
) -> UserResponse:
    return await user_service.get_user(user)


@users_router.put("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    user: UUID = Depends(get_current_user),
) -> UserResponse:
    return await user_service.update_user(user, user_update)


@users_router.delete("/me")
async def delete_user(
    user_service: UserService = Depends(get_user_service),
    user: UUID = Depends(get_current_user),
) -> JSONResponse:
    await user_service.delete_user(user)
    return {"detail": "User deleted successfully"}
