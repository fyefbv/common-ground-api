from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_accept_language,
    get_current_profile,
    get_current_user,
    get_profile_service,
)
from app.schemas.interest import InterestResponse
from app.schemas.profile import (
    ProfileAvatarResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
    UserProfile,
)
from app.schemas.profile_interest import ProfileInterestAdd, ProfileInterestDelete
from app.services.profile import ProfileService

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
    user_id: UUID = Depends(get_current_user),
) -> ProfileResponse:
    profile_create.user_id = user_id
    return await profile_service.create_profile(profile_create)


@profiles_router.get("/me", response_model=list[ProfileResponse])
async def get_user_profiles(
    profile_service: ProfileService = Depends(get_profile_service),
    user_id: UUID = Depends(get_current_user),
) -> list[ProfileResponse]:
    return await profile_service.get_user_profiles(user_id)


@profiles_router.get("/{username}", response_model=ProfileResponse)
async def get_profile(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    _: UUID = Depends(get_current_user),
) -> ProfileResponse:
    return await profile_service.get_profile(username)


@profiles_router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ProfileResponse:
    return await profile_service.update_profile(user_profile.profile_id, profile_update)


@profiles_router.delete("/me")
async def delete_profile(
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    await profile_service.delete_profile(user_profile.profile_id)
    return {"detail": "Profile deleted successfully"}


@profiles_router.post("/me/avatar", response_model=ProfileAvatarResponse)
async def upload_avatar(
    file: UploadFile = File(),
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ProfileAvatarResponse:
    file_data = await file.read()

    return await profile_service.upload_avatar(
        profile_id=user_profile.profile_id,
        file_data=file_data,
        content_type=file.content_type,
    )


@profiles_router.delete("/me/avatar")
async def delete_avatar(
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    await profile_service.delete_avatar(user_profile.profile_id)
    return {"detail": "Profile avatar deleted successfully"}


@profiles_router.get("/{username}/interests", response_model=list[InterestResponse])
async def get_profile_interests(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    accept_language: str = Depends(get_accept_language),
    _: UUID = Depends(get_current_user),
) -> list[InterestResponse]:
    return await profile_service.get_profile_interests(username, accept_language)


@profiles_router.post("/me/interests")
async def add_profile_interests(
    profile_interest_add: ProfileInterestAdd,
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    await profile_service.add_profile_interests(
        profile_id=user_profile.profile_id, profile_interest_add=profile_interest_add
    )
    return {"detail": "Profile interests added successfully"}


@profiles_router.delete("/me/interests")
async def delete_profile_interests(
    profile_interest_delete: ProfileInterestDelete,
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    await profile_service.delete_profile_interests(
        profile_id=user_profile.profile_id,
        profile_interest_delete=profile_interest_delete,
    )
    return {"detail": "Profile interests deleted successfully"}
