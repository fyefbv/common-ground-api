from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import app_logger


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик для ошибок валидации Pydantic"""

    app_logger.warning(f"Ошибка валидации запроса: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "validation_error",
                "message": "Validation failed",
                "details": exc.errors(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Обработчик для ошибок базы данных"""

    app_logger.error(f"Ошибка базы данных: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "database_error",
                "message": "Database error occurred",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик для непредвиденных исключений"""
    
    app_logger.error(f"Непредвиденная ошибка: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "internal_server_error",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )