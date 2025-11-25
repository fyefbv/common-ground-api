from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.file import FileTooLargeError, UnsupportedMediaTypeError
from app.core.logger import app_logger


async def unsupported_media_type_handler(
    request: Request, exc: UnsupportedMediaTypeError
):
    app_logger.error(f"Ошибка: неподдерживаемый тип медиа")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "unsupported_media_type",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def file_too_large_handler(request: Request, exc: FileTooLargeError):
    app_logger.error(f"Ошибка: файл слишком большой")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "file_too_large",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
