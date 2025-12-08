from app.db.models.user import User
from app.repositories.base import Repository


class UserRepository(Repository):
    model = User
