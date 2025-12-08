from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.schemas.interest import InterestResponse


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
