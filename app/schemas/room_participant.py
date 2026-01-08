from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.room_participant import RoomParticipantRole


class RoomParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: UUID
    room_id: UUID
    role: RoomParticipantRole
    joined_at: datetime
    is_online: bool
    is_muted: bool
    is_banned: bool


class RoomKickRequest(BaseModel):
    profile_id: UUID
    reason: str | None = None
