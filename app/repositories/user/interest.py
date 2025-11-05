from uuid import UUID

from sqlalchemy import select

from app.db.models.user import Interest
from app.repositories.base import Repository


class InterestRepository(Repository):
    """
    Репозиторий для работы с интересами.
    Наследует базовый репозиторий и использует модель Interest.
    """

    model = Interest

    async def find_all_with_localization(self, accept_language: str) -> list[Interest]:
        stmt = select(self.model).where(
            self.model.name_translations[accept_language].astext.is_not(None)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_ids_by_names(
        self, names: list[str], accept_language: str
    ) -> list[UUID]:
        stmt = select(self.model.id).where(
            self.model.name_translations[accept_language].astext.in_(names)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
