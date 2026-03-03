import uuid

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Interest(Base):
    """
    Модель интересов пользователей.

    Хранит интересы с многоязычными переводами для поддержки интернационализации.
    Использует JSONB для хранения переводов в формате {language_code: translation}.

    Attributes:
        id: Уникальный идентификатор интереса (UUID)
        name_translations: Словарь с переводами названия интереса на разные языки
                   (ключ - код языка, значение - перевод)
    """

    __tablename__ = "interests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name_translations: Mapped[dict] = mapped_column(JSONB, unique=True, nullable=False)
