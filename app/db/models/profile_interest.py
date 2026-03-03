import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProfileInterest(Base):
    """
    Модель связи между профилями и интересами.

    Промежуточная таблица, реализующая связь "многие ко многим" между профилями
    пользователей и их интересами. Один профиль может иметь несколько интересов,
    и один интерес может принадлежать нескольким профилям.

    Attributes:
        profile_id: Идентификатор профиля пользователя (часть составного первичного ключа)
        interest_id: Идентификатор интереса (часть составного первичного ключа)
    """

    __tablename__ = "profile_interests"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    interest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interests.id", ondelete="CASCADE"),
        primary_key=True,
    )
