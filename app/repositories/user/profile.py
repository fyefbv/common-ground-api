from sqlalchemy import select

from app.db.models.user import Interest, Profile, ProfileInterest
from app.repositories.base import Repository


class ProfileRepository(Repository):
    """
    Репозиторий для работы с профилями.
    Наследует базовый репозиторий и использует модель Profile.
    """

    model = Profile

    async def get_profile_interests(
        self, username: str, accept_language: str
    ) -> list[Interest]:
        stmt = (
            select(Interest)
            .join(ProfileInterest, ProfileInterest.interest_id == Interest.id)
            .join(self.model, self.model.id == ProfileInterest.profile_id)
            .where(self.model.username == username)
            .where(Interest.name_translations[accept_language].astext.is_not(None))
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
