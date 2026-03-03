import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Room(Base):
    """
    Модель комнат для постоянного общения.

    Представляет постоянные чат-комнаты, организованные вокруг конкретных тем или интересов.
    Комнаты могут быть публичными или приватными и имеют различных участников с разными ролями.

    Attributes:
        id: Уникальный идентификатор комнаты (UUID)
        name: Уникальное название комнаты (максимум 100 символов)
        description: Описание комнаты (необязательное поле)
        primary_interest_id: Основной интерес, связанный с комнатой
        creator_id: Идентификатор создателя комнаты
        tags: Список тегов для категоризации комнаты
        max_participants: Максимальное количество участников
        is_private: Флаг приватности комнаты
        created_at: Временная метка создания комнаты
        updated_at: Временная метка последнего обновления комнаты
    """

    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_interest_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, default=list, index=True
    )
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    is_private: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
