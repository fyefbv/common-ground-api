from fastapi import FastAPI

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from .system import validation_exception_handler
from .system import sqlalchemy_exception_handler
from .system import general_exception_handler
from .user import (
    email_exists_handler,
    user_not_found_handler
)
from app.core.exceptions.user import (
    UserNotFoundError,
    EmailAlreadyExistsError
)


def setup_exception_handlers(app: FastAPI):
    """Настройка всех обработчиков исключений"""

    # Пользовательские исключения
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(EmailAlreadyExistsError, email_exists_handler)
    
    # Системные исключения
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)