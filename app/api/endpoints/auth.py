from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_user_service
from app.core.auth import create_tokens, refresh_tokens
from app.schemas.auth import TokenRefresh, TokenResponse
from app.schemas.user import UserCreate, UserLogin
from app.services.user import UserService

auth_router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@auth_router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_create: UserCreate, user_service: UserService = Depends(get_user_service)
) -> TokenResponse:
    user = await user_service.create_user(user_create)
    if user:
        return create_tokens(user.id)


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin, user_service: UserService = Depends(get_user_service)
) -> TokenResponse:
    user = await user_service.authenticate_user(user_login)
    if user:
        return create_tokens(user.id)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: TokenRefresh) -> TokenResponse:
    return refresh_tokens(refresh_token.token)
