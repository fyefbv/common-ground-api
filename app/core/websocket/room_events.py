from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoomEventType(str, Enum):
    MESSAGE_SENT = "message_sent"
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_DELETED = "message_deleted"

    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    PARTICIPANT_KICKED = "participant_kicked"
    PARTICIPANT_BANNED = "participant_banned"
    PARTICIPANT_ROLE_CHANGED = "participant_role_changed"
    PARTICIPANT_UNBANNED = "participant_unbanned"
    PARTICIPANT_MUTED = "participant_muted"
    PARTICIPANT_UNMUTED = "participant_unmuted"

    ROOM_UPDATED = "room_updated"
    ROOM_DELETED = "room_deleted"

    TYPING_STARTED = "typing_started"
    TYPING_STOPPED = "typing_stopped"

    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    CONNECTION_ESTABLISHED = "connection_established"


class RoomWebSocketMessage(BaseModel):
    type: RoomEventType
    data: dict[str, Any]
    timestamp: datetime
    room_id: UUID | None = None
    sender_profile_id: UUID | None = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid),
        },
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
