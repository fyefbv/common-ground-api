import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChatRouletteSessionStatus(str, Enum):
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    LEFT = "LEFT"
    REPORTED = "REPORTED"
    CANCELLED = "CANCELLED"


class ChatRouletteSession(Base):
    __tablename__ = "chat_roulette_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile1_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile2_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    matched_interest_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ChatRouletteSessionStatus.WAITING.value,
        index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    extension_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rating_from_1_to_2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_from_2_to_1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_reason: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    extension_approved_by_profile1: Mapped[bool] = mapped_column(default=False)
    extension_approved_by_profile2: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
