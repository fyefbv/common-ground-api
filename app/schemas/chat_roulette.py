from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileSummary(BaseModel):
    id: UUID
    username: str
    bio: str | None = None
    reputation_score: float
    avatar_url: str | None = None


class ChatRouletteSearchRequest(BaseModel):
    priority_interest_ids: list[UUID] | None = Field(None)
    max_wait_time_minutes: int = Field(default=10, ge=1, le=30)

    @field_validator("priority_interest_ids")
    @classmethod
    def validate_interest_ids(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError("Maximum 5 priority interests allowed")
        return v


class ChatRouletteSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile1_id: UUID
    profile2_id: UUID | None
    matched_interest_id: UUID | None
    status: str
    duration_minutes: int
    extension_minutes: int | None
    started_at: datetime | None
    expires_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    matched_profile: ProfileSummary | None = None
    common_interests: list[UUID] | None = None
    time_remaining: int | None = None
    extension_approved_by_profile1: bool = False
    extension_approved_by_profile2: bool = False


class ChatRouletteMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Message cannot consist only of whitespace")
        return v


class ChatRouletteMessageResponse(BaseModel):
    session_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime


class SessionExtendResponse(BaseModel):
    session_id: UUID
    extended_minutes: int
    new_expires_at: str


class SessionEndRequest(BaseModel):
    reason: str


class ChatRouletteRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = Field(None, max_length=500)


class ChatRouletteReportRequest(BaseModel):
    reason: str | None = Field(None, max_length=100)
    details: str | None = Field(None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def reason_validation(cls, v):
        if v is not None and len(v) < 10:
            raise ValueError("Reason must be at least 10 characters if provided")
        return v

    @field_validator("details")
    @classmethod
    def details_validation(cls, v):
        if v is not None and len(v) < 20:
            raise ValueError("Details must be at least 20 characters if provided")
        return v


class ChatRouletteStatisticsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    average_rating: float
    completion_rate: float


class ChatRouletteSearchResponse(BaseModel):
    session: ChatRouletteSessionResponse
    immediate_match: bool
    search_id: UUID | None = None
