from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_profile, get_room_service
from app.schemas.profile import UserProfile
from app.schemas.room import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from app.schemas.room_message import (
    RoomMessageCreate,
    RoomMessageListResponse,
    RoomMessageResponse,
    RoomMessageUpdate,
)
from app.schemas.room_participant import (
    ChangeRoleRequest,
    ParticipantModerationRequest,
    RoomKickRequest,
    RoomParticipantResponse,
)
from app.services.room import RoomService

rooms_router = APIRouter(prefix="/rooms", tags=["Комнаты"])


@rooms_router.get("/", response_model=list[RoomResponse])
async def get_rooms(
    query: str | None = Query(None, min_length=2, max_length=100),
    interest_id: UUID | None = Query(None),
    tags: list[str] | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> list[RoomResponse]:
    """
    Выполняет поиск комнат по фильтрам (название, интересы, теги).

    Args:
        query: Поисковый запрос по названию или описанию
        interest_id: Идентификатор интереса для фильтрации
        tags: Список тегов для фильтрации
        limit: Максимальное количество комнат в ответе
        offset: Смещение для пагинации
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        list[RoomResponse]: Список комнат с информацией об участии текущего пользователя
    """
    return await room_service.search_rooms(
        query=query,
        interest_id=interest_id,
        tags=tags,
        is_private=False,
        limit=limit,
        offset=offset,
        profile_id=user_profile.profile_id,
    )


@rooms_router.get("/popular", response_model=list[RoomResponse])
async def get_popular_rooms(
    limit: int = Query(20, ge=1, le=50),
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> list[RoomResponse]:
    """
    Возвращает список самых популярных комнат по количеству участников.

    Args:
        limit: Максимальное количество комнат в ответе
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        list[RoomResponse]: Список популярных комнат
    """
    return await room_service.get_popular_rooms(limit, user_profile.profile_id)


@rooms_router.get("/my", response_model=list[RoomResponse])
async def get_my_rooms(
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> list[RoomResponse]:
    """
    Возвращает комнаты, созданные текущим пользователем.

    Args:
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        list[RoomResponse]: Список комнат, отсортированных по дате создания
    """
    return await room_service.get_user_rooms(user_profile.profile_id)


@rooms_router.post(
    "/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED
)
async def create_room(
    room_create: RoomCreate,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomResponse:
    """
    Создаёт новую комнату от имени текущего пользователя.

    Args:
        room_create: Данные для создания комнаты (название, описание, теги и др.)
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomResponse: Информация о созданной комнате

    Notes:
        - Текущий пользователь становится создателем комнаты.
        - Возвращает статус 201 Created при успехе.
    """
    return await room_service.create_room(room_create, user_profile.profile_id)


@rooms_router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomResponse:
    """
    Возвращает информацию о комнате по её идентификатору.

    Args:
        room_id: Идентификатор комнаты
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomResponse: Данные комнаты с информацией об участии текущего пользователя
    """
    return await room_service.get_room(room_id, user_profile.profile_id)


@rooms_router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    room_update: RoomUpdate,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomResponse:
    """
    Обновляет информацию о комнате (название, описание, теги и др.).

    Args:
        room_id: Идентификатор комнаты
        room_update: Данные для обновления
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomResponse: Обновлённая информация о комнате

    Notes:
        - Только создатель комнаты может её обновлять.
    """
    return await room_service.update_room(
        room_id=room_id, room_update=room_update, profile_id=user_profile.profile_id
    )


@rooms_router.delete("/{room_id}")
async def delete_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Удаляет комнату по её идентификатору.

    Args:
        room_id: Идентификатор комнаты
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе удаления

    Notes:
        - Только создатель комнаты может её удалить.
    """
    await room_service.delete_room(room_id, user_profile.profile_id)
    return {"detail": "Room deleted successfully"}


@rooms_router.post("/{room_id}/join", response_model=RoomResponse)
async def join_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomResponse:
    """
    Добавляет текущего пользователя в комнату в качестве участника.

    Args:
        room_id: Идентификатор комнаты
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomResponse: Обновлённая информация о комнате с данными об участии

    Notes:
        - Нельзя присоединиться к приватным комнатам.
        - Забаненные пользователи не могут присоединиться.
    """
    return await room_service.join_room(room_id, user_profile.profile_id)


@rooms_router.post("/{room_id}/leave")
async def leave_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Убирает текущего пользователя из списка участников комнаты.

    Args:
        room_id: Идентификатор комнаты
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе выхода

    Notes:
        - Создатель комнаты не может её покинуть (только удалить).
    """
    await room_service.leave_room(room_id, user_profile.profile_id)
    return {"detail": "Left room successfully"}


@rooms_router.get(
    "/{room_id}/participants", response_model=list[RoomParticipantResponse]
)
async def get_room_participants(
    room_id: UUID,
    include_banned: bool = Query(False),
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> list[RoomParticipantResponse]:
    """
    Возвращает список участников комнаты.

    Args:
        room_id: Идентификатор комнаты
        include_banned: Включать ли забаненных участников (по умолчанию: False)
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        list[RoomParticipantResponse]: Список участников с ролями и статусами

    Notes:
        - Требуется участие в комнате.
    """
    return await room_service.get_room_participants(
        room_id=room_id,
        profile_id=user_profile.profile_id,
        include_banned=include_banned,
    )


@rooms_router.delete("/{room_id}/participants")
async def kick_participant(
    room_id: UUID,
    kick_request: RoomKickRequest,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Исключает участника из комнаты.

    Args:
        room_id: Идентификатор комнаты
        kick_request: Идентификатор исключаемого участника
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе исключения

    Notes:
        - Требуются права создателя или модератора.
    """
    await room_service.kick_participant(
        room_id=room_id, kick_request=kick_request, profile_id=user_profile.profile_id
    )
    return {"detail": "Participant kicked successfully"}


@rooms_router.get("/{room_id}/messages", response_model=RoomMessageListResponse)
async def get_room_messages(
    room_id: UUID,
    before: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomMessageListResponse:
    """
    Возвращает список сообщений комнаты с поддержкой пагинации.

    Args:
        room_id: Идентификатор комнаты
        before: Временная метка для фильтрации сообщений (опционально)
        limit: Максимальное количество сообщений (по умолчанию: 50)
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomMessageListResponse: Список сообщений с информацией о пагинации

    Notes:
        - Требуется участие в комнате.
    """
    return await room_service.get_room_messages(
        room_id=room_id, profile_id=user_profile.profile_id, before=before, limit=limit
    )


@rooms_router.post("/{room_id}/messages", response_model=RoomMessageResponse)
async def send_message(
    room_id: UUID,
    message_create: RoomMessageCreate,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomMessageResponse:
    """
    Отправляет сообщение в комнату от имени текущего пользователя.

    Args:
        room_id: Идентификатор комнаты
        message_create: Текст сообщения
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomMessageResponse: Информация об отправленном сообщении

    Notes:
        - Требуется участие в комнате.
        - Забаненные или замученные пользователи не могут отправлять сообщения.
    """
    return await room_service.send_message(
        room_id=room_id,
        message_create=message_create,
        profile_id=user_profile.profile_id,
    )


@rooms_router.patch("/messages/{message_id}", response_model=RoomMessageResponse)
async def update_message(
    message_id: UUID,
    message_update: RoomMessageUpdate,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomMessageResponse:
    """
    Обновляет сообщение в комнате.

    Args:
        message_id: Идентификатор сообщения
        message_update: Новый текст сообщения
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomMessageResponse: Обновлённое сообщение

    Notes:
        - Можно обновлять только свои сообщения.
    """
    return await room_service.update_message(
        message_id=message_id,
        message_update=message_update,
        profile_id=user_profile.profile_id,
    )


@rooms_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Удаляет сообщение из комнаты (мягкое удаление).

    Args:
        message_id: Идентификатор сообщения
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе удаления

    Notes:
        - Можно удалять свои сообщения или иметь права модератора/создателя.
    """
    await room_service.delete_message(message_id, user_profile.profile_id)
    return {"detail": "Message deleted successfully"}


@rooms_router.post("/{room_id}/participants/mute")
async def mute_participant(
    room_id: UUID,
    request: ParticipantModerationRequest,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Заглушает участника в комнате.

    Args:
        room_id: Идентификатор комнаты
        request: Идентификатор заглушаемого участника
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе мута

    Notes:
        - Требуются права создателя или модератора.
    """
    await room_service.mute_participant(
        room_id=room_id,
        target_profile_id=request.participant_id,
        profile_id=user_profile.profile_id,
    )

    return {"detail": "Participant muted successfully"}


@rooms_router.post("/{room_id}/participants/unmute")
async def unmute_participant(
    room_id: UUID,
    request: ParticipantModerationRequest,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Снимает мут с участника в комнате.

    Args:
        room_id: Идентификатор комнаты
        request: Идентификатор размучиваемого участника
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе размута
    """
    await room_service.unmute_participant(
        room_id=room_id,
        target_profile_id=request.participant_id,
        profile_id=user_profile.profile_id,
    )

    return {"detail": "Participant unmuted successfully"}


@rooms_router.post("/{room_id}/participants/ban")
async def ban_participant(
    room_id: UUID,
    request: ParticipantModerationRequest,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Банит участника в комнате.

    Args:
        room_id: Идентификатор комнаты
        request: Идентификатор банимого участника
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе бана
    """
    await room_service.ban_participant(
        room_id=room_id,
        target_profile_id=request.participant_id,
        profile_id=user_profile.profile_id,
    )

    return {"detail": "Participant banned successfully"}


@rooms_router.post("/{room_id}/participants/unban")
async def unban_participant(
    room_id: UUID,
    request: ParticipantModerationRequest,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Снимает бан с участника в комнате.

    Args:
        room_id: Идентификатор комнаты
        request: Идентификатор разбаниваемого участника
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе разбана
    """
    await room_service.unban_participant(
        room_id=room_id,
        target_profile_id=request.participant_id,
        profile_id=user_profile.profile_id,
    )

    return {"detail": "Participant unbanned successfully"}


@rooms_router.get("/{room_id}/banned", response_model=list[RoomParticipantResponse])
async def get_banned_participants(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> list[RoomParticipantResponse]:
    """
    Возвращает список забаненных участников в комнате.

    Args:
        room_id: Идентификатор комнаты
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        list[RoomParticipantResponse]: Список забаненных участников

    Notes:
        - Требуются права создателя или модератора.
    """
    banned_participants = await room_service.get_banned_participants(
        room_id, user_profile.profile_id
    )

    return banned_participants


@rooms_router.post(
    "/{room_id}/participants/change-role", response_model=RoomParticipantResponse
)
async def change_participant_role(
    room_id: UUID,
    change_role_request: ChangeRoleRequest,
    room_service: RoomService = Depends(get_room_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> RoomParticipantResponse:
    """
    Изменяет роль участника в комнате (например, на модератора).

    Args:
        room_id: Идентификатор комнаты
        change_role_request: Идентификатор участника и новая роль
        room_service: Сервис для управления комнатами (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        RoomParticipantResponse: Информация об участнике с новой ролью

    Notes:
        - Требуются права создателя комнаты.
    """
    return await room_service.change_participant_role(
        room_id=room_id,
        target_profile_id=change_role_request.target_profile_id,
        new_role=change_role_request.new_role,
        profile_id=user_profile.profile_id,
    )
