from uuid import UUID

from sqlalchemy import delete, insert, select

from app.db.models.user import Interest, Profile, ProfileInterest
from app.repositories.base import Repository


class ProfileRepository(Repository):
    """
    Репозиторий для работы с профилями.
    Наследует базовый репозиторий и использует модель Profile.
    """

    model = Profile

    async def get_profile_interests(self, username: str) -> list[Interest]:
        stmt = (
            select(Interest)
            .join(ProfileInterest, ProfileInterest.interest_id == Interest.id)
            .join(Profile, Profile.id == ProfileInterest.profile_id)
            .where(Profile.username == username)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_profile_interests_by_ids(
        self, profile_id: UUID, interest_ids: list[UUID]
    ) -> None:
        if interest_ids:
            profile_interests_data = [
                {"profile_id": profile_id, "interest_id": interest_id}
                for interest_id in interest_ids
            ]

            stmt = insert(ProfileInterest).values(profile_interests_data)
            await self.session.execute(stmt)

    async def delete_profile_interests_by_ids(
        self, profile_id: UUID, interest_ids: list[UUID]
    ) -> None:
        if interest_ids:
            delete_stmt = delete(ProfileInterest).where(
                ProfileInterest.profile_id == profile_id,
                ProfileInterest.interest_id.in_(interest_ids),
            )
            await self.session.execute(delete_stmt)
