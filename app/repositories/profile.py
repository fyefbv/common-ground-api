from uuid import UUID

from sqlalchemy import select

from app.db.models.interest import Interest
from app.db.models.profile import Profile
from app.db.models.profile_interest import ProfileInterest
from app.repositories.base import Repository


class ProfileRepository(Repository):
    model = Profile

    async def get_profile_interests(
        self, profile_id: UUID, accept_language: str = "en"
    ) -> list[Interest]:
        stmt = (
            select(Interest)
            .join(ProfileInterest, ProfileInterest.interest_id == Interest.id)
            .join(self.model, self.model.id == ProfileInterest.profile_id)
            .where(self.model.id == profile_id)
            .where(Interest.name_translations[accept_language].astext.is_not(None))
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
