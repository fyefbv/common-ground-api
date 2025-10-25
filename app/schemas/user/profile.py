from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    user_id: UUID
    username: str
    bio: str | None = None
    reputation_score: float


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    username: str | None = None
    bio: str | None = None
    reputation_score: float | None = None


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
