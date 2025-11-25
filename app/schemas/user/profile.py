from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileCreate(BaseModel):
    user_id: UUID | None = None
    username: str
    bio: str | None = None
    reputation_score: float | None = None


class ProfileUpdate(BaseModel):
    username: str | None = None
    bio: str | None = None
    reputation_score: float | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    username: str
    bio: str | None = None
    reputation_score: float
    created_at: datetime
    updated_at: datetime
    avatar_url: str | None = None

class ProfileAvatarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avatar_url: str | None = None


class ProfileInterestBase(BaseModel):
    names: set[str]


class ProfileInterestAdd(ProfileInterestBase):
    pass


class ProfileInterestDelete(ProfileInterestBase):
    pass
