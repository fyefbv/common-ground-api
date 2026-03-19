from uuid import UUID

from app.core.exceptions.user import (
    AuthenticationFailedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.logger import app_logger
from app.core.security import get_password_hash, verify_password
from app.db.unit_of_work import UnitOfWork
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate


class UserService:
    """
    Сервис для управления пользователями системы.

    Обеспечивает бизнес-логику для:
    - Регистрации, аутентификации и управления учётными записями
    - Хэширования паролей и проверки аутентификации
    - CRUD-операций над пользователями
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_user(self, user_create: UserCreate) -> UserResponse:
        """
        Создаёт нового пользователя с уникальным email.

        Args:
            user_create: Данные для создания пользователя (email, пароль, имя и др.)

        Returns:
            UserResponse: Информация о созданном пользователе (без пароля)

        Raises:
            UserAlreadyExistsError: Если email уже занят
        """
        app_logger.info(f"Создание пользователя с email: {user_create.email}")
        user_dict: dict = user_create.model_dump()
        user_dict["password_hash"] = get_password_hash(user_dict.pop("password"))
        async with self.uow as uow:
            existing_user = await uow.user.find_one(email=user_create.email)
            if existing_user:
                raise UserAlreadyExistsError(user_create.email)

            user = await uow.user.add_one(user_dict)
            user_to_return = UserResponse.model_validate(user)
            await uow.commit()

            app_logger.info(f"Пользователь создан с ID: {user_to_return.id}")
            return user_to_return

    async def get_user(self, user_id: UUID) -> UserResponse:
        """
        Возвращает информацию о пользователе по его идентификатору.

        Args:
            user_id: Идентификатор пользователя

        Returns:
            UserResponse: Данные пользователя (без пароля)

        Raises:
            UserNotFoundError: Если пользователь не найден
        """
        app_logger.info(f"Получение пользователя с ID: {user_id}")
        async with self.uow as uow:
            user = await uow.user.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id)

            user_to_return = UserResponse.model_validate(user)

            app_logger.info(f"Пользователь найден: {user.email}")
            return user_to_return

    async def get_users(self) -> list[UserResponse]:
        """
        Возвращает список всех пользователей в системе.

        Returns:
            list[UserResponse]: Список пользователей (без паролей)
        """
        app_logger.info("Получение всех пользователей")
        async with self.uow as uow:
            users = await uow.user.find_all()
            users_to_return = [UserResponse.model_validate(user) for user in users]

            app_logger.info(f"Найдено {len(users)} пользователей")
            return users_to_return

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> UserResponse:
        """
        Обновляет данные пользователя (email, имя, пароль и др.).

        Args:
            user_id: Идентификатор пользователя
            user_update: Данные для обновления (пароль хэшируется автоматически)

        Returns:
            UserResponse: Обновлённая информация о пользователе

        Raises:
            UserNotFoundError: Если пользователь не найден
            UserAlreadyExistsError: Если email уже занят другим пользователем
        """
        app_logger.info(f"Обновление пользователя с ID: {user_id}")
        user_dict: dict = user_update.model_dump(exclude_unset=True)

        async with self.uow as uow:
            if "email" in user_dict:
                existing_user = await uow.user.find_one(email=user_dict["email"])
                if existing_user and existing_user.id != user_id:
                    raise UserAlreadyExistsError(user_dict["email"])

            if "password" in user_dict:
                user_dict["password_hash"] = get_password_hash(
                    user_dict.pop("password")
                )

            user = await uow.user.update(user_id, user_dict)
            if not user:
                raise UserNotFoundError(user_id)

            user_to_return = UserResponse.model_validate(user)
            await uow.commit()

            app_logger.info(f"Пользователь с ID {user_id} обновлен")
            return user_to_return

    async def delete_user(self, user_id: UUID) -> None:
        """
        Удаляет пользователя из системы.

        Args:
            user_id: Идентификатор пользователя

        Raises:
            UserNotFoundError: Если пользователь не найден
        """
        app_logger.info(f"Удаление пользователя с ID: {user_id}")
        async with self.uow as uow:
            user = await uow.user.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id)

            await uow.user.delete(user_id)
            await uow.commit()

            app_logger.info(f"Пользователь с ID {user_id} удален")

    async def authenticate_user(self, user_auth: UserLogin) -> UserResponse:
        """
        Аутентифицирует пользователя по email и паролю.

        Args:
            user_auth: Данные для аутентификации (email и пароль)

        Returns:
            UserResponse: Информация о пользователе (без пароля)

        Raises:
            AuthenticationFailedError: Если email или пароль неверны
        """
        app_logger.info(
            f"Попытка аутентификации пользователя с email: {user_auth.email}"
        )
        async with self.uow as uow:
            user = await uow.user.find_one(email=user_auth.email)
            if not user or not verify_password(user_auth.password, user.password_hash):
                raise AuthenticationFailedError()

            user_to_return = UserResponse.model_validate(user)

            app_logger.info(
                f"Успешная аутентификация пользователя с email: {user_auth.email}"
            )
            return user_to_return
