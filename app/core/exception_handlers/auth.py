from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.auth import (
    ExpiredTokenError,
    InvalidTokenError,
    MissingTokenError,
)
from app.core.logger import app_logger


async def invalid_token_handler(request: Request, exc: InvalidTokenError):
    app_logger.error("Предоставлен недействительный токен")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "invalid_token",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def expired_token_handler(request: Request, exc: ExpiredTokenError):
    app_logger.error("Срок действия токена истек")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "expired_token",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def missing_token_handler(request: Request, exc: MissingTokenError):
    app_logger.error("Токен отсутствует")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "missing_token",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
