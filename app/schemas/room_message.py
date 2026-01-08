from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_message_id: UUID | None = None


class RoomMessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class RoomMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    sender_id: UUID
    content: str
    parent_message_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    is_edited: bool
    is_deleted: bool


class RoomMessageListResponse(BaseModel):
    messages: list[RoomMessageResponse]
    total: int
    has_more: bool
