from typing import Any
from uuid import UUID

from app.core.exceptions.user.profile import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfilePermissionError,
)
from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.schemas.user import (
    InterestResponse,
    ProfileCreate,
    ProfileInterestAdd,
    ProfileInterestDelete,
    ProfileInterestResponse,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.user import InterestService


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

            app_logger.info(f"Профиль {username} найден")
            return profile_to_return

    async def get_profiles(self) -> list[ProfileResponse]:
        app_logger.info("Получение всех профилей")
        async with self.uow as uow:
            profiles = await uow.profile.find_all()
            profiles_to_return = [
                ProfileResponse.model_validate(profile) for profile in profiles
            ]

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

            updated_profile = await uow.profile.update(
                profile.id, profile_update.model_dump()
            )
            profile_to_return = ProfileResponse.model_validate(updated_profile)
            await uow.commit()

            app_logger.info(f"Профиль {username} обновлен")
            return profile_to_return

    async def delete_profile(self, username: str, user_id: UUID) -> None:
        app_logger.info(f"Удаление профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            await uow.profile.delete(profile.id)
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
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            profile_interests = await uow.profile.get_profile_interests(username)

            app_logger.info(
                f"Найдено {len(profile_interests)} интересов для профиля: {username}"
            )

            profile_interests_to_return = [
                InterestResponse.model_validate(interest)
                for interest in profile_interests
            ]
            return profile_interests_to_return

    async def add_profile_interests(
        self, username: str, profile_interest_add: ProfileInterestAdd, user_id: UUID
    ) -> None:
        app_logger.info(f"Добавление интересов к профилю: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            if profile.user_id != user_id:
                raise ProfilePermissionError(username)

            profile_interests = await uow.profile.get_profile_interests(username)
            existing_interest_names = [interest.name for interest in profile_interests]

            interests_to_add = [
                name
                for name in profile_interest_add.names
                if name not in existing_interest_names
            ]

            interest_ids = await InterestService.get_interests_ids_by_names(
                interests_to_add, uow.session
            )

            await uow.profile.add_profile_interests_by_ids(profile.id, interest_ids)

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
            existing_interest_names = [interest.name for interest in profile_interests]

            interests_to_delete = [
                name
                for name in profile_interest_delete.names
                if name in existing_interest_names
            ]

            interest_ids = await InterestService.get_interests_ids_by_names(
                interests_to_delete, uow.session
            )

            await uow.profile.delete_profile_interests_by_ids(profile.id, interest_ids)

            await uow.commit()

            app_logger.info(
                f"Удалено {len(interest_ids)} интересов из профиля {username}"
            )
