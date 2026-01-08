from uuid import UUID

from fastapi import Depends, Header, Query

from app.core.auth import decode_jwt, oauth2_scheme
from app.core.config import settings
from app.core.exceptions.auth import MissingTokenError
from app.db.unit_of_work import UnitOfWork
from app.services import InterestService, ProfileService, UserService
from app.services.room import RoomService
from app.utils.object_storage import ObjectStorageService


async def get_unit_of_work() -> UnitOfWork:
    return UnitOfWork()


async def get_object_storage_service() -> ObjectStorageService:
    return ObjectStorageService(
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key_id=settings.S3_ACCESS_KEY_ID,
        secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
    )


async def get_user_service(uow: UnitOfWork = Depends(get_unit_of_work)) -> UserService:
    return UserService(uow)


async def get_profile_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
    object_storage_service: ObjectStorageService = Depends(get_object_storage_service),
) -> ProfileService:
    return ProfileService(uow, object_storage_service)


async def get_interest_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> InterestService:
    return InterestService(uow)


async def get_room_service(uow: UnitOfWork = Depends(get_unit_of_work)) -> RoomService:
    return RoomService(uow)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UUID:
    if not token:
        raise MissingTokenError()

    payload = decode_jwt(token)
    return UUID(payload.get("sub"))


async def get_accept_language(accept_language: str = Header(default="en")):
    return accept_language


async def get_valid_profile_id(
    profile_id: UUID = Query(...),
    user: UUID = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> UUID:
    await profile_service.validate_profile_ownership(profile_id, user)
    return profile_id
