from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions.file import FileTooLargeError, UnsupportedMediaTypeError
from app.core.exceptions.object_storage import (
    ObjectDeleteError,
    ObjectUploadError,
    ObjectListGetError,
)
from app.core.exceptions.user import (
    AuthenticationFailedError,
    ExpiredTokenError,
    InterestNotFoundError,
    InvalidTokenError,
    MissingTokenError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfilePermissionError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

from .file import file_too_large_handler, unsupported_media_type_handler
from .object_storage import (
    object_delete_handler,
    object_upload_handler,
    object_list_get_handler,
)
from .system import (
    general_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from .user import (
    authentication_failed_handler,
    expired_token_handler,
    interest_not_found_handler,
    invalid_token_handler,
    missing_token_handler,
    profile_exists_handler,
    profile_not_found_handler,
    profile_permission_handler,
    user_exists_handler,
    user_not_found_handler,
)


def setup_exception_handlers(app: FastAPI):
    """Настройка всех обработчиков исключений"""

    # Пользовательские исключения
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(UserAlreadyExistsError, user_exists_handler)
    app.add_exception_handler(AuthenticationFailedError, authentication_failed_handler)
    app.add_exception_handler(InvalidTokenError, invalid_token_handler)
    app.add_exception_handler(ExpiredTokenError, expired_token_handler)
    app.add_exception_handler(MissingTokenError, missing_token_handler)
    app.add_exception_handler(InterestNotFoundError, interest_not_found_handler)
    app.add_exception_handler(ProfileNotFoundError, profile_not_found_handler)
    app.add_exception_handler(ProfileAlreadyExistsError, profile_exists_handler)
    app.add_exception_handler(ProfilePermissionError, profile_permission_handler)

    # Системные исключения
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Исключения объектного хранилища
    app.add_exception_handler(ObjectUploadError, object_upload_handler)
    app.add_exception_handler(ObjectDeleteError, object_delete_handler)
    app.add_exception_handler(ObjectListGetError, object_list_get_handler)

    # Файловые исключения
    app.add_exception_handler(UnsupportedMediaTypeError, unsupported_media_type_handler)
    app.add_exception_handler(FileTooLargeError, file_too_large_handler)
