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
    """
    Возвращает список всех профилей в системе.

    Args:
        profile_service: Сервис для управления профилями (инъекция зависимости)
        _: Идентификатор текущего пользователя (требуется аутентификация)

    Returns:
        list[ProfileResponse]: Список профилей с аватарками
    """
    return await profile_service.get_profiles()


@profiles_router.post(
    "/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED
)
async def create_profile(
    profile_create: ProfileCreate,
    profile_service: ProfileService = Depends(get_profile_service),
    user_id: UUID = Depends(get_current_user),
) -> ProfileResponse:
    """
    Создаёт новый профиль для текущего пользователя.

    Args:
        profile_create: Данные для создания профиля (username, биография и др.)
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_id: Идентификатор текущего пользователя (инъекция зависимости)

    Returns:
        ProfileResponse: Информация о созданном профиле

    Notes:
        - Автоматически привязывает профиль к текущему пользователю.
        - Возвращает статус 201 Created при успехе.
    """
    profile_create.user_id = user_id
    return await profile_service.create_profile(profile_create)


@profiles_router.get("/me", response_model=list[ProfileResponse])
async def get_user_profiles(
    profile_service: ProfileService = Depends(get_profile_service),
    user_id: UUID = Depends(get_current_user),
) -> list[ProfileResponse]:
    """
    Возвращает все профили, принадлежащие текущему пользователю.

    Args:
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_id: Идентификатор текущего пользователя (инъекция зависимости)

    Returns:
        list[ProfileResponse]: Список профилей пользователя
    """
    return await profile_service.get_user_profiles(user_id)


@profiles_router.get("/current", response_model=ProfileResponse)
async def get_current_profile_by_token(
    user_profile: UserProfile = Depends(get_current_profile),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """
    Возвращает текущий профиль пользователя по токену.

    Args:
        user_profile: Текущий профиль пользователя (инъекция зависимости)
        profile_service: Сервис для управления профилями (инъекция зависимости)

    Returns:
        ProfileResponse: Данные текущего профиля пользователя
    """
    return await profile_service.get_profile(profile_id=user_profile.profile_id)


@profiles_router.get("/{username}", response_model=ProfileResponse)
async def get_profile(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    _: UUID = Depends(get_current_user),
) -> ProfileResponse:
    """
    Возвращает информацию о профиле по его username.

    Args:
        username: Уникальное имя профиля
        profile_service: Сервис для управления профилями (инъекция зависимости)
        _: Идентификатор текущего пользователя (требуется аутентификация)

    Returns:
        ProfileResponse: Данные профиля с URL аватарки
    """
    return await profile_service.get_profile(username=username)


@profiles_router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ProfileResponse:
    """
    Обновляет данные текущего профиля пользователя.

    Args:
        profile_update: Данные для обновления (биография, интересы и др.)
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        ProfileResponse: Обновлённая информация о профиле
    """
    return await profile_service.update_profile(user_profile.profile_id, profile_update)


@profiles_router.delete("/me")
async def delete_profile(
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Удаляет текущий профиль пользователя вместе с аватаркой и интересами.

    Args:
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе удаления
    """
    await profile_service.delete_profile(user_profile.profile_id)
    return {"detail": "Profile deleted successfully"}


@profiles_router.post("/me/avatar", response_model=ProfileAvatarResponse)
async def upload_avatar_to_me(
    file: UploadFile = File(),
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ProfileAvatarResponse:
    """
    Загружает аватарку для текущего профиля пользователя.

    Args:
        file: Файл аватарки (ожидается изображение)
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        ProfileAvatarResponse: URL загруженной аватарки

    Notes:
        - Поддерживаются изображения до 5MB.
        - Возвращает предподписанный URL для доступа к аватарке.
    """
    file_data = await file.read()

    return await profile_service.upload_avatar(
        profile_id=user_profile.profile_id,
        file_data=file_data,
        content_type=file.content_type,
    )


@profiles_router.post("/{username}/avatar", response_model=ProfileAvatarResponse)
async def upload_avatar_by_username(
    username: str,
    file: UploadFile = File(),
    profile_service: ProfileService = Depends(get_profile_service),
    user_id: UUID = Depends(get_current_user),
) -> ProfileAvatarResponse:
    """
    Загружает аватарку для профиля по его username.

    Args:
        username: Имя профиля
        file: Файл аватарки (ожидается изображение)
        profile_service: Сервис для управления профилями (инъекция зависимости)
        _: Идентификатор текущего пользователя (требуется аутентификация)

    Returns:
        ProfileAvatarResponse: URL загруженной аватарки

    Raises:
        ProfileNotFoundError: Если профиль не найден
        UnsupportedMediaTypeError: Если файл не является изображением
        FileTooLargeError: Если размер файла превышает 5MB
    """
    file_data = await file.read()

    return await profile_service.upload_avatar(
        username=username,
        user_id=user_id,
        file_data=file_data,
        content_type=file.content_type,
    )


@profiles_router.delete("/me/avatar")
async def delete_avatar(
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Удаляет аватарку текущего профиля пользователя.

    Args:
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе удаления
    """
    await profile_service.delete_avatar(user_profile.profile_id)
    return {"detail": "Profile avatar deleted successfully"}


@profiles_router.get("/{username}/interests", response_model=list[InterestResponse])
async def get_profile_interests(
    username: str,
    profile_service: ProfileService = Depends(get_profile_service),
    accept_language: str = Depends(get_accept_language),
    _: UUID = Depends(get_current_user),
) -> list[InterestResponse]:
    """
    Возвращает интересы профиля с локализованными названиями.

    Args:
        username: Имя профиля
        profile_service: Сервис для управления профилями (инъекция зависимости)
        accept_language: Код языка для локализации (например, 'ru')
        _: Идентификатор текущего пользователя (требуется аутентификация)

    Returns:
        list[InterestResponse]: Список интересов с переведёнными названиями
    """
    return await profile_service.get_profile_interests(username, accept_language)


@profiles_router.post("/me/interests")
async def add_profile_interests_to_me(
    profile_interest_add: ProfileInterestAdd,
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Добавляет интересы к текущему профилю пользователя.

    Args:
        profile_interest_add: Список идентификаторов интересов для добавления
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе добавления
    """
    await profile_service.add_profile_interests(
        profile_id=user_profile.profile_id, profile_interest_add=profile_interest_add
    )
    return {"detail": "Profile interests added successfully"}


@profiles_router.post("/{username}/interests")
async def add_profile_interests_by_username(
    username: str,
    profile_interest_add: ProfileInterestAdd,
    profile_service: ProfileService = Depends(get_profile_service),
    user_id: UUID = Depends(get_current_user),
) -> JSONResponse:
    """
    Добавляет интересы к профилю по его username.

    Args:
        username: Имя профиля
        profile_interest_add: Список идентификаторов интересов для добавления
        profile_service: Сервис для управления профилями (инъекция зависимости)
        _: Идентификатор текущего пользователя (требуется аутентификация)

    Returns:
        JSONResponse: Сообщение об успехе добавления

    Raises:
        ProfileNotFoundError: Если профиль не найден
        InterestNotFoundError: Если указан несуществующий интерес
    """
    await profile_service.add_profile_interests(
        username=username, user_id=user_id, profile_interest_add=profile_interest_add
    )
    return {"detail": f"Profile interests added successfully"}


@profiles_router.delete("/me/interests")
async def delete_profile_interests(
    profile_interest_delete: ProfileInterestDelete,
    profile_service: ProfileService = Depends(get_profile_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Удаляет интересы из текущего профиля пользователя.

    Args:
        profile_interest_delete: Список идентификаторов интересов для удаления
        profile_service: Сервис для управления профилями (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе удаления
    """
    await profile_service.delete_profile_interests(
        profile_id=user_profile.profile_id,
        profile_interest_delete=profile_interest_delete,
    )
    return {"detail": "Profile interests deleted successfully"}
