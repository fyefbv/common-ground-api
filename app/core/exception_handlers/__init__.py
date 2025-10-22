from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions.user import (
    AuthenticationFailedError,
    EmailAlreadyExistsError,
    ExpiredTokenError,
    InvalidTokenError,
    MissingTokenError,
    UserNotFoundError,
)

from .system import (
    general_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from .user import (
    authentication_failed_handler,
    email_exists_handler,
    expired_token_handler,
    invalid_token_handler,
    missing_token_handler,
    user_not_found_handler,
)


def setup_exception_handlers(app: FastAPI):
    """Настройка всех обработчиков исключений"""

    # Пользовательские исключения
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(EmailAlreadyExistsError, email_exists_handler)
    app.add_exception_handler(AuthenticationFailedError, authentication_failed_handler)
    app.add_exception_handler(InvalidTokenError, invalid_token_handler)
    app.add_exception_handler(ExpiredTokenError, expired_token_handler)
    app.add_exception_handler(MissingTokenError, missing_token_handler)

    # Системные исключения
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
