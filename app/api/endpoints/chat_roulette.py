from uuid import UUID

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
    return await chat_roulette_service.start_search(
        search_request, user_profile.profile_id
    )


@chat_roulette_router.post("/search/cancel")
async def cancel_search(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
    cancelled = await chat_roulette_service.cancel_search(user_profile.profile_id)
    if cancelled:
        return {"detail": "Search cancelled successfully"}
    return {"detail": "No active search found"}


@chat_roulette_router.get("/session", response_model=None)
async def get_active_session(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ChatRouletteSessionResponse | JSONResponse:
    session = await chat_roulette_service.get_active_session(user_profile.profile_id)
    if session:
        return session
    return {"detail": "No active session found"}


@chat_roulette_router.post("/session/extend", response_model=SessionExtendResponse)
async def extend_session(
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> SessionExtendResponse:
    return await chat_roulette_service.extend_session(user_profile.profile_id)


@chat_roulette_router.post("/session/end")
async def end_session(
    request: SessionEndRequest,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> JSONResponse:
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
    return await chat_roulette_service.get_statistics(user_profile.profile_id)


@chat_roulette_router.post("/messages", response_model=ChatRouletteMessageResponse)
async def send_message(
    message_create: ChatRouletteMessageCreate,
    chat_roulette_service: ChatRouletteService = Depends(get_chat_roulette_service),
    user_profile: UserProfile = Depends(get_current_profile),
) -> ChatRouletteMessageResponse:
    return await chat_roulette_service.send_message(
        user_profile.profile_id, message_create.content
    )
