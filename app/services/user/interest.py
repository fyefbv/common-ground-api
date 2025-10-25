from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.schemas.user import InterestResponse


class InterestService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_interests(self) -> list[InterestResponse]:
        app_logger.info("Получение всех интересов")
        async with self.uow as uow:
            interests = await uow.interest.find_all()
            interests_to_return = [
                InterestResponse.model_validate(interest) for interest in interests
            ]

            app_logger.info(f"Найдено {len(interests_to_return)} интересов")
            return interests_to_return
