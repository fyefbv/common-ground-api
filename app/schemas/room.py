from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(None, max_length=1000)
    primary_interest_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    max_participants: int = Field(default=50, ge=2, le=1000)
    is_private: bool = Field(default=False)

    @field_validator("tags")
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        if any(len(tag) > 50 for tag in v):
            raise ValueError("Tag cannot exceed 50 characters")
        return v


class RoomUpdate(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = Field(None, max_length=1000)
    primary_interest_id: UUID | None = None
    tags: list[str] | None = None
    max_participants: int | None = Field(None, ge=2, le=1000)
    is_private: bool | None = None

    @field_validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            if any(len(tag) > 50 for tag in v):
                raise ValueError("Tag cannot exceed 50 characters")
        return v


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    primary_interest_id: UUID | None = None
    creator_id: UUID
    tags: list[str]
    max_participants: int
    is_private: bool
    participants_count: int
    messages_count: int
    created_at: datetime
    updated_at: datetime
    is_joined: bool | None = None
