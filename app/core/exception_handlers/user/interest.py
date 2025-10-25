from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.user import InterestNotFoundError
from app.core.logger import app_logger


async def interest_not_found_handler(request: Request, exc: InterestNotFoundError):
    app_logger.error(f"Интерес {getattr(exc, "entity_field", "unknown")} не найден")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "interest_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
