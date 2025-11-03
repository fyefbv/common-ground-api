import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd7627c98ded5'
down_revision: Union[str, Sequence[str], None] = '3dbef3c9af77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    interests_table = table(
        'interests',
        column('id', sa.dialects.postgresql.UUID),
        column('name_translations', sa.dialects.postgresql.JSONB)
    )

    translated_interests = [
        {"en": "Programming", "ru": "Программирование"},
        {"en": "Web Development", "ru": "Веб-разработка"},
        {"en": "Mobile App Development", "ru": "Разработка мобильных приложений"},
        {"en": "Artificial Intelligence", "ru": "Искусственный интеллект"},
        {"en": "Machine Learning", "ru": "Машинное обучение"},
        {"en": "Data Science", "ru": "Наука о данных"},
        {"en": "Cybersecurity", "ru": "Кибербезопасность"},
        {"en": "Blockchain", "ru": "Блокчейн"},
        {"en": "Cloud Computing", "ru": "Облачные вычисления"},
        {"en": "DevOps", "ru": "DevOps"},
        {"en": "Painting", "ru": "Живопись"},
        {"en": "Photography", "ru": "Фотография"},
        {"en": "Graphic Design", "ru": "Графический дизайн"},
        {"en": "Digital Art", "ru": "Цифровое искусство"},
        {"en": "Music Production", "ru": "Музыкальное производство"},
        {"en": "Writing", "ru": "Письмо"},
        {"en": "Running", "ru": "Бег"},
        {"en": "Swimming", "ru": "Плавание"},
        {"en": "Cycling", "ru": "Велоспорт"},
        {"en": "Yoga", "ru": "Йога"},
        {"en": "Weightlifting", "ru": "Тяжелая атлетика"},
        {"en": "Martial Arts", "ru": "Боевые искусства"},
        {"en": "Basketball", "ru": "Баскетбол"},
        {"en": "Football", "ru": "Футбол"},
        {"en": "Tennis", "ru": "Теннис"},
        {"en": "Golf", "ru": "Гольф"},
        {"en": "Video Games", "ru": "Видеоигры"},
        {"en": "Board Games", "ru": "Настольные игры"},
        {"en": "Role-Playing Games", "ru": "Ролевые игры"},
        {"en": "Puzzles", "ru": "Головоломки"},
        {"en": "Strategy Games", "ru": "Стратегические игры"},
        {"en": "Cooking", "ru": "Кулинария"},
        {"en": "Baking", "ru": "Выпечка"},
        {"en": "Grilling", "ru": "Гриль"},
        {"en": "Vegan Cuisine", "ru": "Веганская кухня"},
        {"en": "International Cuisine", "ru": "Международная кухня"},
        {"en": "Gardening", "ru": "Садоводство"},
        {"en": "Birdwatching", "ru": "Наблюдение за птицами"},
        {"en": "Camping", "ru": "Кемпинг"},
        {"en": "Fishing", "ru": "Рыбалка"},
        {"en": "Hiking", "ru": "Походы"},
        {"en": "Travel", "ru": "Путешествия"},
        {"en": "Backpacking", "ru": "Бэкпэкинг"},
        {"en": "Cultural Studies", "ru": "Культурные исследования"},
        {"en": "Language Learning", "ru": "Изучение языков"},
        {"en": "History", "ru": "История"},
        {"en": "Physics", "ru": "Физика"},
        {"en": "Chemistry", "ru": "Химия"},
        {"en": "Biology", "ru": "Биология"},
        {"en": "Mathematics", "ru": "Математика"},
        {"en": "Astronomy", "ru": "Астрономия"}
    ]

    op.bulk_insert(
        interests_table,
        [{"id": str(uuid.uuid4()), "name_translations": interest} for interest in translated_interests]
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM interests")
