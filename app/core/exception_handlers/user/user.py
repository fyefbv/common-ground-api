from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.user import UserNotFoundError, EmailAlreadyExistsError
from app.core.logger import app_logger


async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    app_logger.error(f"Пользователь не найден: ID {getattr(exc, "user_id", "unknown")}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "user_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )

async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    app_logger.warning(f"Попытка создания пользователя с существующим email: {getattr(exc, "email", "unknown")}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "email_already_exists", 
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )