from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.profile import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfilePermissionError,
)
from app.core.logger import app_logger


async def profile_not_found_handler(request: Request, exc: ProfileNotFoundError):
    app_logger.error(f"Профиль {getattr(exc, 'entity_field', 'unknown')} не найден")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "profile_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def profile_exists_handler(request: Request, exc: ProfileAlreadyExistsError):
    app_logger.warning(
        f"Попытка создания профиля с существующим username: {getattr(exc, "entity_field", "unknown")}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "profile_already_exists",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def profile_permission_handler(request: Request, exc: ProfilePermissionError):
    app_logger.warning(
        f"Попытка доступа к профилю без прав: {getattr(exc, "profile_field", "unknown")}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "profile_permission_denied",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
