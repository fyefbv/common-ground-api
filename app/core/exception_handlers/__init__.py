from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exception_handlers.auth import (
    expired_token_handler,
    invalid_token_handler,
    missing_token_handler,
)
from app.core.exception_handlers.file import (
    file_too_large_handler,
    unsupported_media_type_handler,
)
from app.core.exception_handlers.interest import interest_not_found_handler
from app.core.exception_handlers.object_storage import (
    object_delete_handler,
    object_list_get_handler,
    object_upload_handler,
)
from app.core.exception_handlers.profile import (
    profile_exists_handler,
    profile_not_found_handler,
    profile_permission_handler,
)
from app.core.exception_handlers.room import (
    message_not_found_handler,
    not_room_member_handler,
    participant_banned_handler,
    participant_muted_handler,
    participant_not_found_handler,
    room_exists_handler,
    room_full_handler,
    room_not_found_handler,
    room_permission_handler,
    room_private_handler,
)
from app.core.exception_handlers.system import (
    general_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from app.core.exception_handlers.user import (
    authentication_failed_handler,
    user_exists_handler,
    user_not_found_handler,
)
from app.core.exceptions.auth import (
    ExpiredTokenError,
    InvalidTokenError,
    MissingTokenError,
)
from app.core.exceptions.file import FileTooLargeError, UnsupportedMediaTypeError
from app.core.exceptions.interest import InterestNotFoundError
from app.core.exceptions.object_storage import (
    ObjectDeleteError,
    ObjectListGetError,
    ObjectUploadError,
)
from app.core.exceptions.profile import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfilePermissionError,
)
from app.core.exceptions.room import (
    NotRoomMemberError,
    ParticipantBannedError,
    ParticipantMutedError,
    RoomAlreadyExistsError,
    RoomFullError,
    RoomMessageNotFoundError,
    RoomNotFoundError,
    RoomParticipantNotFoundError,
    RoomPermissionError,
    RoomPrivateError,
)
from app.core.exceptions.user import (
    AuthenticationFailedError,
    UserAlreadyExistsError,
    UserNotFoundError,
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

    # Исключения комнат
    app.add_exception_handler(RoomNotFoundError, room_not_found_handler)
    app.add_exception_handler(RoomAlreadyExistsError, room_exists_handler)
    app.add_exception_handler(RoomPermissionError, room_permission_handler)
    app.add_exception_handler(RoomFullError, room_full_handler)
    app.add_exception_handler(RoomPrivateError, room_private_handler)
    app.add_exception_handler(NotRoomMemberError, not_room_member_handler)
    app.add_exception_handler(ParticipantBannedError, participant_banned_handler)
    app.add_exception_handler(ParticipantMutedError, participant_muted_handler)
    app.add_exception_handler(
        RoomParticipantNotFoundError, participant_not_found_handler
    )
    app.add_exception_handler(RoomMessageNotFoundError, message_not_found_handler)

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
