from app.db.models.user import User
from app.repositories.base_repository import Repository


class UserRepository(Repository):
    model = User