from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user, get_profile_service
from app.schemas.user import (
    InterestResponse,
    ProfileCreate,
    ProfileInterestAdd,
    ProfileInterestDelete,
    ProfileInterestResponse,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.user import ProfileService

profiles_router = APIRouter(prefix="/profiles", tags=["Профили"])


@profiles_router.get("/", response_model=list[ProfileResponse])
async def get_profiles(
    profile_service: ProfileService = Depends(get_profile_service),
    _: UUID = Depends(get_current_user),
) -> list[ProfileResponse]:
    return await profile_service.get_profiles()


@profiles_router.post(
    "/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED
)
async def create_profile(
    profile_create: ProfileCreate,
    profile_service: ProfileService = Depends(get_profile_service),
    user: UUID = Depends(get_current_user),
) -> ProfileResponse:
    profile_create.user_id = user
    return await profile_service.create_profile(profile_create)


@profiles_router.get("/me", response_model=list[ProfileResponse])
async def get_user_profiles(
    profile_service: ProfileService = Depends(get_profile_service),
    user: UUID = Depends(get_current_user),
) -> list[ProfileResponse]:
    return await profile_service.get_user_profiles(user)


@profiles_router.get("/{username}", response_model=ProfileResponse)
async def get_profile(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    _: UUID = Depends(get_current_user),
) -> ProfileResponse:
    return await profile_service.get_profile(username)


@profiles_router.put("/{username}", response_model=ProfileResponse)
async def update_profile(
    username: str,
    profile_update: ProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
    user: UUID = Depends(get_current_user),
) -> ProfileResponse:
    return await profile_service.update_profile(username, profile_update, user)


@profiles_router.delete("/{username}")
async def delete_profile(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    user: UUID = Depends(get_current_user),
) -> JSONResponse:
    await profile_service.delete_profile(username, user)
    return {"detail": "Profile deleted successfully"}


@profiles_router.get("/{username}/interests", response_model=list[InterestResponse])
async def get_profile_interests(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    _: UUID = Depends(get_current_user),
) -> list[InterestResponse]:
    return await profile_service.get_profile_interests(username)


@profiles_router.post("/{username}/interests")
async def add_profile_interests(
    username: str,
    profile_interest_add: ProfileInterestAdd,
    profile_service: ProfileService = Depends(get_profile_service),
    user: UUID = Depends(get_current_user),
) -> JSONResponse:
    await profile_service.add_profile_interests(username, profile_interest_add, user)
    return {"detail": "Profile interests added successfully"}


@profiles_router.delete("/{username}/interests")
async def delete_profile_interests(
    username: str,
    profile_interest_delete: ProfileInterestDelete,
    profile_service: ProfileService = Depends(get_profile_service),
    user: UUID = Depends(get_current_user),
) -> JSONResponse:
    await profile_service.delete_profile_interests(
        username, profile_interest_delete, user
    )
    return {"detail": "Profile interests deleted successfully"}
