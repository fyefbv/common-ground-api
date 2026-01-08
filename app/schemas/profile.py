from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileBase(BaseModel):
    bio: str | None = Field(None, max_length=2000)
    reputation_score: float | None = Field(None, ge=0.0, le=5.0)


class ProfileCreate(ProfileBase):
    user_id: UUID | None = None
    username: str = Field(..., min_length=3, max_length=40)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers and underscores"
            )
        if v.startswith("_") or v.endswith("_"):
            raise ValueError("Username cannot start or end with underscore")
        return v


class ProfileUpdate(ProfileBase):
    username: str | None = Field(None, min_length=3, max_length=40)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not v.replace("_", "").isalnum():
                raise ValueError(
                    "Username can only contain letters, numbers and underscores"
                )
            if v.startswith("_") or v.endswith("_"):
                raise ValueError("Username cannot start or end with underscore")
        return v


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
