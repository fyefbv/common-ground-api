import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RoomParticipantRole(str, Enum):
    """
    Роли участников комнаты.

    CREATOR: Создатель комнаты (имеет все права)
    MODERATOR: Модератор (может управлять участниками)
    MEMBER: Обычный участник
    """

    CREATOR = "CREATOR"
    MODERATOR = "MODERATOR"
    MEMBER = "MEMBER"


class RoomParticipant(Base):
    """
    Модель участников комнатного чата.

    Промежуточная таблица, реализующая связь "многие ко многим" между комнатами
    и профилями пользователей. Хранит информацию о ролях, статусах и времени
    присоединения участников.

    Attributes:
        room_id: Идентификатор комнаты (часть составного первичного ключа)
        profile_id: Идентификатор профиля участника (часть составного первичного ключа)
        role: Роль участника в комнате
        joined_at: Время присоединения к комнате
        is_muted: Флаг, указывающий заглушен ли участник
        is_banned: Флаг, указывающий забанен ли участник
    """

    __tablename__ = "room_participants"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RoomParticipantRole.MEMBER.value, index=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_muted: Mapped[bool] = mapped_column(default=False)
    is_banned: Mapped[bool] = mapped_column(default=False)
