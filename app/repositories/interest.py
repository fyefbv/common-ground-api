from sqlalchemy import UUID, select

from app.db.models.interest import Interest
from app.repositories.base import Repository


class InterestRepository(Repository):
    model = Interest

    async def find_all_with_localization(self, accept_language: str) -> list[Interest]:
        stmt = select(self.model).where(
            self.model.name_translations[accept_language].astext.is_not(None)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_ids_with_localization(
        self, ids: list[UUID], accept_language: str
    ) -> list[Interest]:
        stmt = select(self.model).where(
            self.model.id.in_(ids),
            self.model.name_translations[accept_language].astext.is_not(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
