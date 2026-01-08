from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

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
from app.core.logger import app_logger


async def room_not_found_handler(request: Request, exc: RoomNotFoundError):
    app_logger.error(f"Комната {getattr(exc, 'entity_field', 'unknown')} не найдена")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "room_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def participant_not_found_handler(
    request: Request, exc: RoomParticipantNotFoundError
):
    app_logger.error(
        f"Участник комнаты {getattr(exc, 'entity_field', 'unknown')} не найден"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "participant_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def message_not_found_handler(request: Request, exc: RoomMessageNotFoundError):
    app_logger.error(
        f"Сообщение комнаты {getattr(exc, 'entity_field', 'unknown')} не найдено"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "message_not_found",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def room_exists_handler(request: Request, exc: RoomAlreadyExistsError):
    app_logger.warning(
        f"Попытка создания комнаты с существующим именем: {getattr(exc, 'entity_field', 'unknown')}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "room_already_exists",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def room_permission_handler(request: Request, exc: RoomPermissionError):
    app_logger.warning(f"Отказ в доступе к комнате: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "room_permission_denied",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def room_full_handler(request: Request, exc: RoomFullError):
    app_logger.warning("Попытка присоединиться к заполненной комнате")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "room_full",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def room_private_handler(request: Request, exc: RoomPrivateError):
    app_logger.warning("Попытка присоединиться к приватной комнате")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "room_private",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def not_room_member_handler(request: Request, exc: NotRoomMemberError):
    app_logger.warning("Попытка доступа не участника комнаты")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "not_room_member",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def participant_banned_handler(request: Request, exc: ParticipantBannedError):
    app_logger.warning("Попытка доступа забаненного участника")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "participant_banned",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def participant_muted_handler(request: Request, exc: ParticipantMutedError):
    app_logger.warning("Попытка отправки сообщения замученным участником")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "participant_muted",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
