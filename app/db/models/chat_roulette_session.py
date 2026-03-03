import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChatRouletteSessionStatus(str, Enum):
    """
    Статусы сессий чат-рулетки.

    WAITING - ожидание партнера
    ACTIVE - активная сессия
    COMPLETED - успешно завершена
    LEFT - один из участников покинул сессию
    REPORTED - сессия завершена по жалобе
    CANCELLED - сессия отменена
    """

    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    LEFT = "LEFT"
    REPORTED = "REPORTED"
    CANCELLED = "CANCELLED"


class ChatRouletteSession(Base):
    """
    Модель сессии чат-рулетки.

    Хранит информацию о сессиях случайного чата между двумя профилями,
    включая статусы, временные метки и рейтинги.

    Attributes:
        id: Уникальный идентификатор сессии (UUID)
        profile1_id: Идентификатор первого профиля участника сессии
        profile2_id: Идентификатор второго профиля участника сессии (опционально, если сессия в статусе ожидания)
        matched_interest_id: Идентификатор интереса, по которому произошло совпадение профилей
        status: Текущий статус сессии (WAITING, ACTIVE, COMPLETED, LEFT, REPORTED, CANCELLED)
        duration_minutes: Длительность сессии в минутах (по умолчанию 5)
        extension_minutes: Дополнительное время, на которое продлена сессия (опционально)
        started_at: Временная метка начала сессии
        expires_at: Временная метка истечения срока действия сессии
        ended_at: Временная метка завершения сессии
        rating_from_1_to_2: Оценка, которую поставил первый профиль второму (1-5, опционально)
        rating_from_2_to_1: Оценка, которую поставил второй профиль первому (1-5, опционально)
        end_reason: Причина завершения сессии (опционально)
        created_at: Временная метка создания сессии
        extension_approved_by_profile1: Флаг, указывающий, что первый профиль одобрил продление сессии
        extension_approved_by_profile2: Флаг, указывающий, что второй профиль одобрил продление сессии
        updated_at: Временная метка последнего обновления сессии
    """

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
