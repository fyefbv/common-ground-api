from typing import Any
from uuid import UUID

from app.core.exceptions.user.profile import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)
from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.schemas.user import (
    InterestResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)


class ProfileService:
    """
    Сервис для управления профилями.
    Обеспечивает создание, получение, обновление и удаление профилей.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_profile(self, profile_create: ProfileCreate) -> ProfileResponse:
        app_logger.info(f"Создание профиля с user_id: {profile_create.user_id}")
        async with self.uow as uow:
            existing_profile = await uow.profile.get_one(profile_create.username)
            if existing_profile:
                raise ProfileAlreadyExistsError(profile_create.username)

            profile = await uow.profile.add_one(profile_create.model_dump())
            profile_to_return = ProfileResponse.model_validate(profile)
            await uow.commit()

            app_logger.info(f"Профиль создан с ID: {profile_to_return.id}")
            return profile_to_return

    async def get_profile(self, identifier: Any) -> ProfileResponse:
        app_logger.info(f"Получение профиля: {identifier}")
        async with self.uow as uow:
            profile = await uow.profile.get_one(identifier)
            if not profile:
                raise ProfileNotFoundError(identifier)

            profile_to_return = ProfileResponse.model_validate(profile)

            app_logger.info(f"Профиль {identifier} найден")
            return profile_to_return

    async def update_profile(
        self, username: str, profile_update: ProfileUpdate
    ) -> ProfileResponse:
        app_logger.info(f"Обновление профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.update(username, profile_update.model_dump())
            if not profile:
                raise ProfileNotFoundError(username)

            profile_to_return = ProfileResponse.model_validate(profile)
            await uow.commit()

            app_logger.info(f"Профиль {username} обновлен")
            return profile_to_return

    async def delete_profile(self, username: str) -> None:
        app_logger.info(f"Удаление профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.get_one(username)
            if not profile:
                raise ProfileNotFoundError(username)

            await uow.profile.delete(username)
            await uow.commit()

            app_logger.info(f"Профиль {username} удален")

    async def get_user_profiles(self, user_id: UUID) -> list[ProfileResponse]:
        app_logger.info(f"Получение всех профилей пользователя с ID: {user_id}")
        async with self.uow as uow:
            profiles = await uow.profile.find_all(user_id=user_id)
            profiles_to_return = [
                ProfileResponse.model_validate(profile) for profile in profiles
            ]

            app_logger.info(
                f"Найдено {len(profiles)} профилей для пользователя с ID {user_id}"
            )
            return profiles_to_return

    async def get_profile_interests(self, username: str) -> list[InterestResponse]:
        app_logger.info(f"Получение интересов профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.get_one(username)
            if not profile:
                raise ProfileNotFoundError(username)

            interests = profile.interests
            interest_objects = [pi.interest for pi in interests]

            app_logger.info(
                f"Найдено {len(interest_objects)} интересов для профиля: {username}"
            )
            interests_to_return = [
                InterestResponse.model_validate(interest)
                for interest in interest_objects
            ]

            return interests_to_return
