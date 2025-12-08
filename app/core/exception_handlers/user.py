from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.user import (
    AuthenticationFailedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.logger import app_logger


async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    app_logger.error(
        f"Пользователь {getattr(exc, "entity_field", "unknown")} не найден"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "user_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
    app_logger.warning(
        f"Попытка создания пользователя с существующим email: {getattr(exc, "entity_field", "unknown")}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "user_already_exists",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def authentication_failed_handler(
    request: Request, exc: AuthenticationFailedError
):
    app_logger.warning("Неудачная попытка аутентификации")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "authentication_failed",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
