from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_room_service, get_valid_profile_id
from app.schemas.room import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from app.schemas.room_message import (
    RoomMessageCreate,
    RoomMessageListResponse,
    RoomMessageResponse,
    RoomMessageUpdate,
)
from app.schemas.room_participant import (
    RoomKickRequest,
    RoomParticipantResponse,
)
from app.services.room import RoomService

rooms_router = APIRouter(prefix="/rooms", tags=["Комнаты"])


@rooms_router.get("/", response_model=list[RoomResponse])
async def get_rooms(
    query: str | None = Query(None, min_length=2, max_length=100),
    interest_id: UUID | None = Query(None),
    tags: list[str] | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> list[RoomResponse]:
    return await room_service.search_rooms(
        query=query,
        interest_id=interest_id,
        tags=tags,
        is_private=False,
        limit=limit,
        offset=offset,
        profile_id=profile_id,
    )


@rooms_router.get("/popular", response_model=list[RoomResponse])
async def get_popular_rooms(
    limit: int = Query(20, ge=1, le=50),
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> list[RoomResponse]:
    return await room_service.get_popular_rooms(limit, profile_id)


@rooms_router.get("/my", response_model=list[RoomResponse])
async def get_my_rooms(
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> list[RoomResponse]:
    return await room_service.get_user_rooms(profile_id)


@rooms_router.post(
    "/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED
)
async def create_room(
    room_create: RoomCreate,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomResponse:
    return await room_service.create_room(room_create, profile_id)


@rooms_router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomResponse:
    return await room_service.get_room(room_id, profile_id)


@rooms_router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    room_update: RoomUpdate,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomResponse:
    return await room_service.update_room(
        room_id=room_id, room_update=room_update, profile_id=profile_id
    )


@rooms_router.delete("/{room_id}")
async def delete_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> JSONResponse:
    await room_service.delete_room(room_id, profile_id)
    return {"detail": "Room deleted successfully"}


@rooms_router.post("/{room_id}/join", response_model=RoomResponse)
async def join_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomResponse:
    return await room_service.join_room(room_id, profile_id)


@rooms_router.post("/{room_id}/leave")
async def leave_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> JSONResponse:
    await room_service.leave_room(room_id, profile_id)
    return {"detail": "Left room successfully"}


@rooms_router.get(
    "/{room_id}/participants", response_model=list[RoomParticipantResponse]
)
async def get_room_participants(
    room_id: UUID,
    include_banned: bool = Query(False),
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> list[RoomParticipantResponse]:
    return await room_service.get_room_participants(
        room_id=room_id, profile_id=profile_id, include_banned=include_banned
    )


@rooms_router.delete("/{room_id}/participants")
async def kick_participant(
    room_id: UUID,
    kick_request: RoomKickRequest,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> JSONResponse:
    await room_service.kick_participant(
        room_id=room_id, kick_request=kick_request, profile_id=profile_id
    )
    return {"detail": "Participant kicked successfully"}


@rooms_router.get("/{room_id}/messages", response_model=RoomMessageListResponse)
async def get_room_messages(
    room_id: UUID,
    before: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomMessageListResponse:
    return await room_service.get_room_messages(
        room_id=room_id, profile_id=profile_id, before=before, limit=limit
    )


@rooms_router.post("/{room_id}/messages", response_model=RoomMessageResponse)
async def send_message(
    room_id: UUID,
    message_create: RoomMessageCreate,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomMessageResponse:
    return await room_service.send_message(
        room_id=room_id, message_create=message_create, profile_id=profile_id
    )


@rooms_router.put("/messages/{message_id}", response_model=RoomMessageResponse)
async def update_message(
    message_id: UUID,
    message_update: RoomMessageUpdate,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> RoomMessageResponse:
    return await room_service.update_message(
        message_id=message_id, message_update=message_update, profile_id=profile_id
    )


@rooms_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID,
    room_service: RoomService = Depends(get_room_service),
    profile_id: UUID = Depends(get_valid_profile_id),
) -> JSONResponse:
    await room_service.delete_message(message_id, profile_id)
    return {"detail": "Message deleted successfully"}
