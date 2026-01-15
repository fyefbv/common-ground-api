from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_profile_service, get_user_service
from app.core.auth import create_tokens, refresh_tokens
from app.schemas.auth import ProfileTokenCreate, TokenRefresh, TokenResponse
from app.schemas.user import UserCreate, UserLogin
from app.services.profile import ProfileService
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


@auth_router.post("/select-profile", response_model=TokenResponse)
async def select_profile(
    profile_token_create: ProfileTokenCreate,
    user_id: UUID = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> TokenResponse:
    await profile_service.validate_profile_ownership(
        profile_token_create.profile_id, user_id
    )
    return create_tokens(user_id, profile_token_create.profile_id)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: TokenRefresh) -> TokenResponse:
    return refresh_tokens(refresh_token.token)
