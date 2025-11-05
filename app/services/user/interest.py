from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.repositories.user import InterestRepository
from app.schemas.user import InterestResponse


class InterestService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_interests(self, accept_language: str) -> list[InterestResponse]:
        app_logger.info("Получение всех интересов")
        async with self.uow as uow:
            interests = await uow.interest.find_all_with_localization(accept_language)
            interests_to_return = [
                InterestResponse(
                    id=interest.id, name=interest.name_translations[accept_language]
                )
                for interest in interests
            ]

            app_logger.info(f"Найдено {len(interests_to_return)} интересов")
            return interests_to_return

    @staticmethod
    async def get_interests_ids_by_names(
        names: list[str], accept_language: str, session: AsyncSession
    ) -> list[UUID]:
        app_logger.info(f"Получение ID интересов по именам: {names}")

        interest_repo = InterestRepository(session)
        interest_ids = await interest_repo.find_ids_by_names(names, accept_language)

        app_logger.info(f"ID интересов найдены: {interest_ids}")
        return interest_ids
