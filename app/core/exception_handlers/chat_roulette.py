from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.chat_roulette import (
    AlreadyInSearchError,
    AlreadyInSessionError,
    AlreadyRatedError,
    CannotRateNonCompletedSessionError,
    CannotRateYourselfError,
    ExtensionNotApprovedError,
    NoActiveSearchError,
    NoActiveSessionError,
    NoMatchingFoundError,
    PartnerNotFoundError,
    SessionAlreadyEndedError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.core.logger import app_logger


async def already_in_search_handler(request: Request, exc: AlreadyInSearchError):
    app_logger.warning("Попытка начать новый поиск при активном поиске")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "already_in_search",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def already_in_session_handler(request: Request, exc: AlreadyInSessionError):
    app_logger.warning("Попытка начать новый поиск при активной сессии")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "already_in_session",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def no_active_search_handler(request: Request, exc: NoActiveSearchError):
    app_logger.error("Активный поиск не найден")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "no_active_search",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def no_active_session_handler(request: Request, exc: NoActiveSessionError):
    app_logger.error("Активная сессия не найдена")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "no_active_session",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def session_not_found_handler(request: Request, exc: SessionNotFoundError):
    app_logger.error(f"Сессия чат-рулетки не найдена")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "session_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def partner_not_found_handler(request: Request, exc: PartnerNotFoundError):
    app_logger.error("Партнер не найден")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "partner_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def session_expired_handler(request: Request, exc: SessionExpiredError):
    app_logger.warning("Попытка доступа к истекшей сессии")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "session_expired",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def session_already_ended_handler(
    request: Request, exc: SessionAlreadyEndedError
):
    app_logger.warning("Попытка доступа к уже завершенной сессии")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "session_already_ended",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def cannot_rate_yourself_handler(request: Request, exc: CannotRateYourselfError):
    app_logger.warning("Попытка самопроверки")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "cannot_rate_yourself",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def already_rated_handler(request: Request, exc: AlreadyRatedError):
    app_logger.warning("Попытка повторной оценки партнера")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "already_rated",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def extension_not_approved_handler(
    request: Request, exc: ExtensionNotApprovedError
):
    app_logger.warning("Попытка продлить сессию без подтверждения партнера")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "extension_not_approved",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def cannot_rate_non_completed_session_handler(
    request: Request, exc: CannotRateNonCompletedSessionError
):
    app_logger.warning(
        f"Попытка оценить партнера в сессии со статусом {exc.current_status}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "cannot_rate_non_completed_session",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def no_matching_found_handler(request: Request, exc: NoMatchingFoundError):
    app_logger.warning("Не удалось найти собеседника для поиска")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "no_matching_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
