from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

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


class ParticipantModerationRequest(BaseModel):
    participant_id: UUID


class ChangeRoleRequest(BaseModel):
    target_profile_id: UUID
    new_role: RoomParticipantRole

    @field_validator("new_role")
    @classmethod
    def validate_role(cls, v):
        if v not in [RoomParticipantRole.MEMBER, RoomParticipantRole.MODERATOR]:
            raise ValueError("Role must be either MEMBER or MODERATOR")
        return v
