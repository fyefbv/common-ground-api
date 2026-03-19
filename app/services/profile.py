from uuid import UUID

from app.core.exceptions.file import FileTooLargeError, UnsupportedMediaTypeError
from app.core.exceptions.interest import InterestNotFoundError
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
from app.utils.object_storage import ObjectStorageService


class ProfileService:
    """
    Сервис для управления профилями пользователей, их интересами и аватарками.

    Обеспечивает бизнес-логику для:
    - Создания, обновления и удаления профилей
    - Управления аватарками (загрузка, удаление, получение URL)
    - Работы с интересами профилей (добавление, удаление, получение)
    - Проверки прав доступа к профилям
    """

    def __init__(self, uow: UnitOfWork, oss: ObjectStorageService):
        self.uow = uow
        self.oss = oss

    async def create_profile(self, profile_create: ProfileCreate) -> ProfileResponse:
        """
        Создаёт новый профиль пользователя с уникальным именем.

        Args:
            profile_create: Данные для создания профиля (username, user_id, биография и др.)

        Returns:
            ProfileResponse: Информация о созданном профиле

        Raises:
            ProfileAlreadyExistsError: Если username уже занят
        """
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
        """
        Возвращает информацию о профиле по его username.

        Args:
            username: Уникальное имя профиля

        Returns:
            ProfileResponse: Данные профиля, включая URL аватарки

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        app_logger.info(f"Получение профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            profile_to_return = ProfileResponse.model_validate(profile)
            profile_to_return.avatar_url = await self.oss.get_avatar_url(profile.id)

            app_logger.info(f"Профиль {username} найден")
            return profile_to_return

    async def get_profiles(self) -> list[ProfileResponse]:
        """
        Возвращает список всех профилей в системе.

        Returns:
            list[ProfileResponse]: Список профилей с URL аватарок
        """
        app_logger.info("Получение всех профилей")
        async with self.uow as uow:
            profiles = await uow.profile.find_all()
            profile_ids = [profile.id for profile in profiles]
            avatar_urls = await self.oss.list_avatars(profile_ids)

            profiles_to_return = []
            for profile in profiles:
                profile_to_return = ProfileResponse.model_validate(profile)
                profile_to_return.avatar_url = avatar_urls.get(profile.id)

                profiles_to_return.append(profile_to_return)

            app_logger.info(f"Найдено {len(profiles)} профилей")
            return profiles_to_return

    async def update_profile(
        self, profile_id: UUID, profile_update: ProfileUpdate
    ) -> ProfileResponse:
        """
        Обновляет данные профиля (биографию, интересы, настройки и др.).

        Args:
            profile_id: Идентификатор профиля
            profile_update: Данные для обновления

        Returns:
            ProfileResponse: Обновлённая информация о профиле

        Raises:
            ProfileNotFoundError: Если профиль не найден
            ProfileAlreadyExistsError: Если username уже занят другим профилем
        """
        app_logger.info(f"Обновление профиля: {profile_id}")
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            update_dict = profile_update.model_dump(exclude_unset=True)

            if "username" in update_dict:
                existing_profile = await uow.profile.find_one(
                    username=update_dict["username"]
                )
                if existing_profile and existing_profile.id != profile_id:
                    raise ProfileAlreadyExistsError(update_dict["username"])

            updated_profile = await uow.profile.update(profile.id, update_dict)

            profile_to_return = ProfileResponse.model_validate(updated_profile)
            profile_to_return.avatar_url = await self.oss.get_avatar_url(profile.id)

            await uow.commit()

            app_logger.info(f"Профиль {profile_id} обновлен")
            return profile_to_return

    async def upload_avatar(
        self, profile_id: UUID, file_data: bytes, content_type: str
    ) -> ProfileAvatarResponse:
        """
        Загружает аватарку для профиля в объектное хранилище.

        Args:
            profile_id: Идентификатор профиля
            file_data: Двоичные данные файла аватарки
            content_type: MIME-тип файла (например, 'image/jpeg')

        Returns:
            ProfileAvatarResponse: URL загруженной аватарки

        Raises:
            ProfileNotFoundError: Если профиль не найден
            UnsupportedMediaTypeError: Если файл не является изображением
            FileTooLargeError: Если размер файла превышает 5MB
        """
        app_logger.info(f"Загрузка аватарки для профиля: {profile_id}")
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            if not content_type.startswith("image/"):
                raise UnsupportedMediaTypeError("File must be an image")

            if len(file_data) > 5 * 1024 * 1024:
                raise FileTooLargeError("File is too large. Maximum size: 5MB")

            avatar_url = await self.oss.upload_avatar(profile_id, file_data)

            avatar_to_return = ProfileAvatarResponse.model_validate(
                {"avatar_url": avatar_url}
            )

            return avatar_to_return

    async def delete_avatar(self, profile_id: UUID) -> None:
        """
        Удаляет аватарку профиля из объектного хранилища.

        Args:
            profile_id: Идентификатор профиля

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        app_logger.info(f"Удаление аватарки для профиля: {profile_id}")
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            await self.oss.delete_avatar(profile_id)

    async def delete_profile(self, profile_id: UUID) -> None:
        """
        Удаляет профиль, его аватарку и все связанные интересы.

        Args:
            profile_id: Идентификатор профиля

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        app_logger.info(f"Удаление профиля: {profile_id}")
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            existing_avatar = await self.oss.avatar_exists(profile_id)

            if existing_avatar:
                await self.oss.delete_avatar(profile_id)
            else:
                app_logger.warning(f"Не удалось удалить аватарку профиля {profile_id}")

            await uow.profile_interest.delete_by_profile_id(profile_id)
            await uow.profile.delete(profile_id)
            await uow.commit()

            app_logger.info(f"Профиль {profile_id} удален")

    async def get_user_profiles(self, user_id: UUID) -> list[ProfileResponse]:
        """
        Возвращает все профили, принадлежащие одному пользователю.

        Args:
            user_id: Идентификатор пользователя

        Returns:
            list[ProfileResponse]: Список профилей пользователя
        """
        app_logger.info(f"Получение всех профилей пользователя с ID: {user_id}")
        async with self.uow as uow:
            profiles = await uow.profile.find_all(user_id=user_id)
            profile_ids = [profile.id for profile in profiles]
            avatar_urls = await self.oss.list_avatars(profile_ids)

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
        """
        Возвращает список интересов профиля с локализованными названиями.

        Args:
            username: Имя профиля
            accept_language: Код языка для локализации названий интересов (например, 'ru')

        Returns:
            list[InterestResponse]: Список интересов с переведёнными названиями

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        app_logger.info(f"Получение интересов профиля: {username}")
        async with self.uow as uow:
            profile = await uow.profile.find_one(username=username)
            if not profile:
                raise ProfileNotFoundError(username)

            profile_interests = await uow.profile.get_profile_interests(
                profile.id, accept_language
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
        profile_id: UUID,
        profile_interest_add: ProfileInterestAdd,
    ) -> None:
        """
        Добавляет новые интересы к профилю, избегая дубликатов.

        Args:
            profile_id: Идентификатор профиля
            profile_interest_add: Список идентификаторов интересов для добавления

        Raises:
            ProfileNotFoundError: Если профиль не найден
            InterestNotFoundError: Если указан несуществующий интерес
        """
        app_logger.info(f"Добавление интересов к профилю: {profile_id}")
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            profile_interests = await uow.profile.get_profile_interests(profile_id)

            existing_interest_ids = [interest.id for interest in profile_interests]

            interests_to_add = []
            for interest_id in profile_interest_add.ids:
                if interest_id not in existing_interest_ids:
                    interest = await uow.interest.get_by_id(interest_id)
                    if not interest:
                        raise InterestNotFoundError(interest_id)
                    interests_to_add.append(interest_id)

            await uow.profile_interest.add_by_ids(profile_id, interests_to_add)

            await uow.commit()

            app_logger.info(f"Интересы добавлены к профилю {profile_id}")

    async def delete_profile_interests(
        self,
        profile_id: UUID,
        profile_interest_delete: ProfileInterestDelete,
    ) -> None:
        """
        Удаляет указанные интересы из профиля.

        Args:
            profile_id: Идентификатор профиля
            profile_interest_delete: Список идентификаторов интересов для удаления

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        app_logger.info(f"Удаление интересов профиля: {profile_id}")
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            profile_interests = await uow.profile.get_profile_interests(profile_id)

            existing_interest_ids = [interest.id for interest in profile_interests]

            interests_to_delete = [
                id for id in profile_interest_delete.ids if id in existing_interest_ids
            ]

            await uow.profile_interest.delete_by_ids(profile_id, interests_to_delete)

            await uow.commit()

            app_logger.info(
                f"Удалено {len(profile_interest_delete.ids)} интересов из профиля {profile_id}"
            )

    async def validate_profile_ownership(self, profile_id: UUID, user_id: UUID) -> None:
        """
        Проверяет, принадлежит ли профиль указанному пользователю.

        Args:
            profile_id: Идентификатор профиля
            user_id: Идентификатор пользователя

        Raises:
            ProfileNotFoundError: Если профиль не найден
            ProfilePermissionError: Если профиль принадлежит другому пользователю
        """
        app_logger.info(
            f"Проверка принадлежности профиля {profile_id} пользователю {user_id}"
        )
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(str(profile_id))

            if profile.user_id != user_id:
                raise ProfilePermissionError(str(profile_id))
