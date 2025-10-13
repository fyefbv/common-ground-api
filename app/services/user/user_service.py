from uuid import UUID

from app.db.unit_of_work import UnitOfWork
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.exceptions.user import EmailAlreadyExistsError, UserNotFoundError
from app.core.logger import app_logger


class UserService:
    """
    Сервис для управления пользователями.
    Обеспечивает создание, получение, обновление и удаление пользователей.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_user(self, user_create: UserCreate) -> UserResponse:
        app_logger.info(f"Создание пользователя с email: {user_create.email}")
        user_dict: dict = user_create.model_dump()
        user_dict["password_hash"] = user_dict.pop("password")
        async with self.uow as uow:
            existing_user = await uow.user.find_one(email=user_create.email)
            if existing_user:
                raise EmailAlreadyExistsError(user_create.email)
            
            user = await uow.user.add_one(user_dict)
            user_to_return = UserResponse.model_validate(user)
            await uow.commit()
        
            app_logger.info(f"Пользователь создан с ID: {user_to_return.id}")
            return user_to_return

    async def get_user(self, user_id: UUID) -> UserResponse:
        app_logger.info(f"Получение пользователя с ID: {user_id}")
        async with self.uow as uow:
            user = await uow.user.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id)
                
            user_to_return = UserResponse.model_validate(user)

            app_logger.info(f"Пользователь найден: {user.email}")
            return user_to_return

    async def get_users(self) -> list[UserResponse]:
        app_logger.info("Получение всех пользователей")
        async with self.uow as uow:
            users = await uow.user.find_all()
            users_to_return = [UserResponse.model_validate(user) for user in users]

            app_logger.info(f"Найдено {len(users)} пользователей")
            return users_to_return

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> UserResponse:
        app_logger.info(f"Обновление пользователя с ID: {user_id}")
        user_dict: dict = user_update.model_dump()
        if "password" in user_dict:
            user_dict["password_hash"] = user_dict.pop("password")
        async with self.uow as uow:
            user = await uow.user.update(user_id, user_dict)
            if not user:
                raise UserNotFoundError(user_id)
            
            user_to_return = UserResponse.model_validate(user)
            await uow.commit()

            app_logger.info(f"Пользователь с ID {user_id} обновлен")
            return user_to_return

    async def delete_user(self, user_id: UUID) -> None:
        app_logger.info(f"Удаление пользователя с ID: {user_id}")
        async with self.uow as uow:
            user = await uow.user.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id)
            
            await uow.user.delete(user_id)
            await uow.commit()

            app_logger.info(f"Пользователь с ID {user_id} удален")