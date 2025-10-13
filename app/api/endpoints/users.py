from fastapi import APIRouter, Depends,status
from uuid import UUID

from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user.user_service import UserService
from app.api.dependencies import get_user_service


users_router = APIRouter(prefix="/users", tags=["Пользователи"])

@users_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, 
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await user_service.create_user(user)

@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID, 
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await user_service.get_user(user_id)

@users_router.get("/", response_model=list[UserResponse])
async def get_users(
    user_service: UserService = Depends(get_user_service)
) -> list[UserResponse]:
    return await user_service.get_users()

@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID, 
    user_update: UserUpdate, 
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await user_service.update_user(user_id, user_update)

@users_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID, 
    user_service: UserService = Depends(get_user_service)
) -> dict:
    await user_service.delete_user(user_id)
    return {"detail": "User deleted successfully"}