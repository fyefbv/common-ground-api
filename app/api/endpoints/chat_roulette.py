from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_chat_roulette_service,
    get_current_profile,
)
from app.schemas.chat_roulette import (
    ChatRouletteMessageCreate,
    ChatRouletteMessageResponse,
    ChatRouletteRatingRequest,
    ChatRouletteReportRequest,
    ChatRouletteSearchRequest,
    ChatRouletteSearchResponse,
    ChatRouletteSessionResponse,
    ChatRouletteStatisticsResponse,
    SessionEndRequest,
    SessionExtendResponse,
)
from app.schemas.profile import UserProfile
from app.services.chat_roulette import ChatRouletteService

chat_roulette_router = APIRouter(prefix="/chat-roulette", tags=["Чат-рулетка"])


@chat_roulette_router.post(
    "/search",
    response_model=ChatRouletteSearchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_search(
    search_request: ChatRouletteSearchRequest,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ChatRouletteSearchResponse:
    """
    Начинает поиск партнёра для чат-рулетки.

    Args:
        search_request: Параметры поиска (интересы)
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        ChatRouletteSearchResponse: Информация о найденном партнёре или статусе поиска

    Notes:
        - Создаёт новую сессию поиска.
        - Возвращает статус 201 Created при успешном запуске.
    """
    return await chat_roulette_service.start_search(
        search_request, user_profile.profile_id
    )


@chat_roulette_router.post("/search/cancel")
async def cancel_search(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Отменяет текущий поиск партнёра для чат-рулетки.

    Args:
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе или отсутствии активного поиска
    """
    cancelled = await chat_roulette_service.cancel_search(user_profile.profile_id)
    if cancelled:
        return {"detail": "Search cancelled successfully"}
    return {"detail": "No active search found"}


@chat_roulette_router.get("/session", response_model=None)
async def get_active_session(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ChatRouletteSessionResponse | JSONResponse:
    """
    Возвращает информацию о текущей активной сессии чат-рулетки.

    Args:
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        ChatRouletteSessionResponse | JSONResponse: Данные сессии или сообщение об её отсутствии
    """
    session = await chat_roulette_service.get_active_session(user_profile.profile_id)
    if session:
        return session
    return {"detail": "No active session found"}


@chat_roulette_router.post("/session/extend", response_model=SessionExtendResponse)
async def extend_session(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> SessionExtendResponse:
    """
    Продлевает время текущей сессии чат-рулетки.

    Args:
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        SessionExtendResponse: Новое время истечения сессии
    """
    return await chat_roulette_service.extend_session(user_profile.profile_id)


@chat_roulette_router.post("/session/end")
async def end_session(
    request: SessionEndRequest,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Завершает текущую сессию чат-рулетки с указанием причины.

    Args:
        request: Причина завершения сессии
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе или неудаче завершения сессии
    """
    ended = await chat_roulette_service.end_session(
        user_profile.profile_id, request.reason
    )
    if ended:
        return {"detail": "Session ended successfully"}
    return {"detail": "Failed to end session"}


@chat_roulette_router.post("/rate")
async def rate_partner(
    rating_request: ChatRouletteRatingRequest,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Ставит оценку партнёру по чат-рулетке.

    Args:
        rating_request: Оценка (рейтинг и комментарий)
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе или неудаче отправки оценки
    """
    rated = await chat_roulette_service.rate_partner(
        user_profile.profile_id, rating_request
    )
    if rated:
        return {"detail": "Rating submitted successfully"}
    return {"detail": "Failed to submit rating"}


@chat_roulette_router.post("/report")
async def report_partner(
    report_request: ChatRouletteReportRequest,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    """
    Отправляет жалобу на партнёра в чат-рулетке.

    Args:
        report_request: Причина жалобы и дополнительные данные
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        JSONResponse: Сообщение об успехе или неудаче отправки жалобы
    """
    reported = await chat_roulette_service.report_partner(
        user_profile.profile_id, report_request
    )
    if reported:
        return {"detail": "Report submitted successfully"}
    return {"detail": "Failed to submit report"}


@chat_roulette_router.get("/statistics", response_model=ChatRouletteStatisticsResponse)
async def get_statistics(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ChatRouletteStatisticsResponse:
    """
    Возвращает статистику чат-рулетки для текущего профиля.

    Args:
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        ChatRouletteStatisticsResponse: Статистика сессий, оценок и жалоб
    """
    return await chat_roulette_service.get_statistics(user_profile.profile_id)


@chat_roulette_router.post("/messages", response_model=ChatRouletteMessageResponse)
async def send_message(
    message_create: ChatRouletteMessageCreate,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ChatRouletteMessageResponse:
    """
    Отправляет сообщение партнёру в текущей сессии чат-рулетки.

    Args:
        message_create: Текст сообщения
        chat_roulette_service: Сервис чат-рулетки (инъекция зависимости)
        user_profile: Текущий профиль пользователя (инъекция зависимости)

    Returns:
        ChatRouletteMessageResponse: Информация об отправленном сообщении
    """
    return await chat_roulette_service.send_message(
        user_profile.profile_id, message_create.content
    )
