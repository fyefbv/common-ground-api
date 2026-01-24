import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChatRouletteSearch(Base):
    __tablename__ = "chat_roulette_searches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    priority_interest_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    search_score: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    search_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    max_wait_time_minutes: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
