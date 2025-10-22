from app.db.models.user import Profile
from app.repositories.base import Repository


class ProfileRepository(Repository):
    """
    Репозиторий для работы с профилями.
    Наследует базовый репозиторий и использует модель Profile.
    """

    model = Profile
