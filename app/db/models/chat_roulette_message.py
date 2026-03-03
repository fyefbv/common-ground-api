import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChatRouletteMessage(Base):
    """
    Модель сообщений чат-рулетки.

    Хранит текстовые сообщения, отправленные между участниками во время сессий чат-рулетки.
    Каждое сообщение привязано к конкретной сессии и профилю отправителя.

    Attributes:
        id: Уникальный идентификатор сообщения (UUID)
        session_id: Идентификатор сессии чат-рулетки, к которой принадлежит сообщение
        sender_profile_id: Идентификатор профиля отправителя сообщения
        content: Текстовое содержимое сообщения
        created_at: Временная метка создания сообщения (с учетом часового пояса)
    """

    __tablename__ = "chat_roulette_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_roulette_sessions.id", ondelete="CASCADE")
    )
    sender_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
