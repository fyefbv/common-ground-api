from uuid import UUID

from app.core.exceptions.file import FileTooLargeError, UnsupportedMediaTypeError
from app.core.exceptions.profile import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfilePermissionError,
)
from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.schemas.interest import InterestResponse
from app.schemas.profile import (
    ProfileAvatarResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.schemas.profile_interest import ProfileInterestAdd, ProfileInterestDelete
from app.services.interest import InterestService
from app.utils.object_storage import ObjectStorageService


class ProfileService:
    def __init__(self, uow: UnitOfWork, object_storage_service: ObjectStorageService):
        self.uow = uow
        self.object_storage_service = object_storage_service

    async def create_profile(self, profile_create: ProfileCreate) -> ProfileResponse:
        app_logger.info(f"Создание профиля с user_id: {profile_create.user_id}")
        async with self.uow as uow:
            existing_profile = await uow.profile.find_one(
                username=profile_create.username
            )
            if existing_profile:
                raise ProfileAlreadyExistsError(profile_create.username)

            profile = await uow.profile.add_one(profile_create.model_dump())
            profile_to_return = ProfileResponse.model_validate(profile)
            await uow.commit()

            app_logger.info(f"Профиль создан с ID: {profile_to_return.id}")
            return profile_to_return

    async def get_profile(self, username: str) -> ProfileResponse:
        app_logger.info(f"Получение профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            profile_to_return = ProfileResponse.model_validate(profile)
            profile_to_return.avatar_url = (
                await self.object_storage_service.get_avatar_url(profile.id)
            )

            app_logger.info(f"Профиль {username} найден")
            return profile_to_return

    async def get_profiles(self) -> list[ProfileResponse]:
        app_logger.info("Получение всех профилей")
        async with self.uow as uow:
            profiles = await uow.profile.find_all()
            profile_ids = [profile.id for profile in profiles]
            avatar_urls = await self.object_storage_service.list_avatars(profile_ids)

            profiles_to_return = []
            for profile in profiles:
                profile_to_return = ProfileResponse.model_validate(profile)
                profile_to_return.avatar_url = avatar_urls.get(profile.id)

                profiles_to_return.append(profile_to_return)

            app_logger.info(f"Найдено {len(profiles)} профилей")
            return profiles_to_return

    async def update_profile(
        self, username: str, profile_update: ProfileUpdate, user_id: UUID
    ) -> ProfileResponse:
        app_logger.info(f"Обновление профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            update_dict = profile_update.model_dump(exclude_unset=True)
            updated_profile = await uow.profile.update(profile.id, update_dict)

            profile_to_return = ProfileResponse.model_validate(updated_profile)
            profile_to_return.avatar_url = (
                await self.object_storage_service.get_avatar_url(profile.id)
            )

            await uow.commit()

            app_logger.info(f"Профиль {username} обновлен")
            return profile_to_return

    async def upload_avatar(
        self, username: str, user_id: UUID, file_data: bytes, content_type: str
    ) -> ProfileAvatarResponse:
        app_logger.info(f"Загрузка аватарки для профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            if not content_type.startswith("image/"):
                raise UnsupportedMediaTypeError("File must be an image")

            if len(file_data) > 5 * 1024 * 1024:
                raise FileTooLargeError("File is too large. Maximum size: 5MB")

            avatar_url = await self.object_storage_service.upload_avatar(
                profile.id, file_data
            )

            avatar_to_return = ProfileAvatarResponse.model_validate(
                {"avatar_url": avatar_url}
            )

            return avatar_to_return

    async def delete_avatar(self, username: str, user_id: UUID) -> None:
        app_logger.info(f"Удаление аватарки для профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            await self.object_storage_service.delete_avatar(profile.id)

    async def delete_profile(self, username: str, user_id: UUID) -> None:
        app_logger.info(f"Удаление профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            existing_avatar = await self.object_storage_service.avatar_exists(
                profile.id
            )

            if existing_avatar:
                await self.object_storage_service.delete_avatar(profile.id)
            else:
                app_logger.warning(f"Не удалось удалить аватарку профиля {username}")

            await uow.profile_interest.delete_by_profile_id(profile.id)
            await uow.profile.delete(profile.id)
            await uow.commit()

            app_logger.info(f"Профиль {username} удален")

    async def get_user_profiles(self, user_id: UUID) -> list[ProfileResponse]:
        app_logger.info(f"Получение всех профилей пользователя с ID: {user_id}")
        async with self.uow as uow:
            profiles = await uow.profile.find_all(user_id=user_id)
            profile_ids = [profile.id for profile in profiles]
            avatar_urls = await self.object_storage_service.list_avatars(profile_ids)

            profiles_to_return = []
            for profile in profiles:
                profile_to_return = ProfileResponse.model_validate(profile)
                profile_to_return.avatar_url = avatar_urls.get(profile.id)

                profiles_to_return.append(profile_to_return)

            app_logger.info(
                f"Найдено {len(profiles)} профилей для пользователя с ID {user_id}"
            )
            return profiles_to_return

    async def get_profile_interests(
        self, username: str, accept_language: str
    ) -> list[InterestResponse]:
        app_logger.info(f"Получение интересов профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            profile_interests = await uow.profile.get_profile_interests(
                username, accept_language
            )

            app_logger.info(
                f"Найдено {len(profile_interests)} интересов для профиля: {username}"
            )

            profile_interests_to_return = [
                InterestResponse(
                    id=interest.id, name=interest.name_translations[accept_language]
                )
                for interest in profile_interests
            ]
            return profile_interests_to_return

    async def add_profile_interests(
        self,
        username: str,
        profile_interest_add: ProfileInterestAdd,
        user_id: UUID,
    ) -> None:
        app_logger.info(f"Добавление интересов к профилю: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            profile_interests = await uow.profile.get_profile_interests(username)

            existing_interest_ids = [interest.id for interest in profile_interests]

            interests_to_add = [
                id for id in profile_interest_add.ids if id not in existing_interest_ids
            ]

            await uow.profile_interest.add_by_ids(profile.id, interests_to_add)

            await uow.commit()

            app_logger.info(f"Интересы добавлены к профилю {username}")

    async def delete_profile_interests(
        self,
        username: str,
        profile_interest_delete: ProfileInterestDelete,
        user_id: UUID,
    ) -> None:
        app_logger.info(f"Удаление всех интересов профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            profile_interests = await uow.profile.get_profile_interests(username)

            existing_interest_ids = [interest.id for interest in profile_interests]

            interests_to_delete = [
                id for id in profile_interest_delete.ids if id in existing_interest_ids
            ]

            await uow.profile_interest.delete_by_ids(profile.id, interests_to_delete)

            await uow.commit()

            app_logger.info(
                f"Удалено {len(profile_interest_delete.ids)} интересов из профиля {username}"
            )
