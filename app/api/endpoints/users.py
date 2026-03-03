from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user, get_user_service
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

users_router = APIRouter(prefix="/users", tags=["Пользователи"])


@users_router.get("/me", response_model=UserResponse)
async def get_user(
    user_service: UserService = Depends(get_user_service),
    user_id: UUID = Depends(get_current_user),
) -> UserResponse:
    """
    Возвращает информацию о текущем пользователе.

    Args:
        user_service: Сервис для управления пользователями (инъекция зависимости)
        user_id: Идентификатор текущего пользователя (из JWT, инъекция зависимости)

    Returns:
        UserResponse: Данные пользователя (без пароля)
    """
    return await user_service.get_user(user_id)


@users_router.patch("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    user_id: UUID = Depends(get_current_user),
) -> UserResponse:
    """
    Обновляет данные текущего пользователя (email, имя, пароль).

    Args:
        user_update: Данные для обновления
        user_service: Сервис для управления пользователями (инъекция зависимости)
        user_id: Идентификатор текущего пользователя (из JWT, инъекция зависимости)

    Returns:
        UserResponse: Обновлённая информация о пользователе
    """
    return await user_service.update_user(user_id, user_update)


@users_router.delete("/me")
async def delete_user(
    user_service: UserService = Depends(get_user_service),
    user_id: UUID = Depends(get_current_user),
) -> JSONResponse:
    """
    Удаляет учётную запись текущего пользователя.

    Args:
        user_service: Сервис для управления пользователями (инъекция зависимости)
        user_id: Идентификатор текущего пользователя (из JWT, инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе удаления
    """
    await user_service.delete_user(user_id)
    return {"detail": "User deleted successfully"}
