import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Profile(Base):
    """
    Модель профиля пользователя.

    Содержит публичную информацию о пользователе, такую как имя пользователя, биография и репутация.
    Один пользователь может иметь несколько профилей.

    Attributes:
        id: Уникальный идентификатор профиля (UUID)
        user_id: Идентификатор пользователя, к которому относится профиль
        username: Уникальное имя пользователя (отображаемое имя, максимум 40 символов)
        bio: Биография или описание профиля (опционально, текстовое поле)
        reputation_score: Рейтинг репутации профиля (влияет на подбор в чат-рулетке, индексируется, по умолчанию 3.0)
        created_at: Временная метка создания профиля
        updated_at: Временная метка последнего обновления профиля
    """

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    username: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    reputation_score: Mapped[float] = mapped_column(
        Float, nullable=False, index=True, default=3.0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
