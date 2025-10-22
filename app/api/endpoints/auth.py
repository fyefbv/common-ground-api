from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_user_service
from app.core.auth import create_tokens, refresh_tokens
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.user import UserService

auth_router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@auth_router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user: UserCreate, user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(user)


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin, user_service: UserService = Depends(get_user_service)
):
    user = await user_service.authenticate_user(user_login)
    if user:
        return create_tokens(user_login.email)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: TokenRefresh):
    return refresh_tokens(refresh_token.token)
