from app.db.models.user import User
from app.repositories.base_repository import Repository


class UserRepository(Repository):
    """
    Репозиторий для работы с пользователями.
    Наследует базовый репозиторий и использует модель User.
    """
    model = User