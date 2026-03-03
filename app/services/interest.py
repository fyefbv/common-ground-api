from app.core.logger import app_logger
from app.db.unit_of_work import UnitOfWork
from app.schemas.interest import InterestResponse


class InterestService:
    """
    Сервис для работы с интересами профилей.

    Обеспечивает доступ к мультиязычным интересам для профилей пользователей.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_interests(self, accept_language: str) -> list[InterestResponse]:
        """
        Возвращает список всех интересов с локализацией для указанного языка.

        Args:
            accept_language: Код языка для локализации названий интересов

        Returns:
            list[InterestResponse]: Список интересов с локализованными названиями
        """
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
