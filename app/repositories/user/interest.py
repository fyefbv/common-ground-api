from app.db.models.user import Interest
from app.repositories.base import Repository


class InterestRepository(Repository):
    """
    Репозиторий для работы с интересами.
    Наследует базовый репозиторий и использует модель Interest.
    """

    model = Interest
