"""filling_the_interests table

Revision ID: d7627c98ded5
Revises: 1af074cd48d0
Create Date: 2025-10-29 14:12:04.347628

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd7627c98ded5'
down_revision: Union[str, Sequence[str], None] = '1af074cd48d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

interests = [
    # Технологии
    "Программирование",
    "Веб-разработка",
    "Разработка мобильных приложений",
    "Искусственный интеллект",
    "Машинное обучение",
    "Наука о данных",
    "Кибербезопасность",
    "Блокчейн",
    "Облачные вычисления",
    "DevOps",

    # Искусство и творчество
    "Живопись",
    "Фотография",
    "Графический дизайн",
    "Цифровое искусство",
    "Музыкальное производство",
    "Письмо",

    # Спорт и фитнес
    "Бег",
    "Плавание",
    "Велоспорт",
    "Йога",
    "Тяжелая атлетика",
    "Боевые искусства",
    "Баскетбол",
    "Футбол",
    "Теннис",
    "Гольф",

    # Игры
    "Видеоигры",
    "Настольные игры",
    "Ролевые игры",
    "Головоломки",
    "Стратегические игры",

    # Еда и кулинария
    "Кулинария",
    "Выпечка",
    "Гриль",
    "Веганская кухня",
    "Международная кухня",

    # Природа и активный отдых
    "Садоводство",
    "Наблюдение за птицами",
    "Кемпинг",
    "Рыбалка",
    "Походы",

    # Путешествия и культура
    "Путешествия",
    "Бэкпэкинг",
    "Культурные исследования",
    "Изучение языков",
    "История",

    # Образование и наука
    "Физика",
    "Химия",
    "Биология",
    "Математика",
    "Астрономия"
]

def upgrade() -> None:
    """Upgrade schema."""
    interests_table = table(
        'interests',
        column('id', sa.dialects.postgresql.UUID),
        column('name', sa.String(40))
    )

    op.bulk_insert(
        interests_table,
        [{"id": str(uuid.uuid4()), "name": name} for name in interests]
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM interests")
