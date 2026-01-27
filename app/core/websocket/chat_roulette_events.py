from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatRouletteEventType(str, Enum):
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"

    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_EXTENDED = "session_extended"
    SESSION_EXPIRED = "session_expired"

    TIMER_UPDATE = "timer_update"
    TIME_ALMOST_UP = "time_almost_up"

    EXTENSION_REQUESTED = "extension_requested"
    EXTENSION_APPROVED = "extension_approved"
    EXTENSION_REJECTED = "extension_rejected"
    EXTENSION_CANCELLED = "extension_cancelled"

    CONNECTION_ESTABLISHED = "connection_established"
    PARTNER_CONNECTED = "partner_connected"
    PARTNER_DISCONNECTED = "partner_disconnected"

    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class ChatRouletteWebSocketMessage(BaseModel):
    type: ChatRouletteEventType
    data: dict[str, Any]
    timestamp: datetime
    session_id: UUID | None = None
    sender_profile_id: UUID | None = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid),
        },
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
