from uuid import UUID

from sqlalchemy import delete, insert

from app.db.models.profile_interest import ProfileInterest
from app.repositories.base import Repository


class ProfileInterestRepository(Repository):
    model = ProfileInterest

    async def add_by_ids(self, profile_id: UUID, interest_ids: list[UUID]) -> None:
        if interest_ids:
            profile_interests_data = [
                {"profile_id": profile_id, "interest_id": interest_id}
                for interest_id in interest_ids
            ]

            stmt = insert(self.model).values(profile_interests_data)
            await self.session.execute(stmt)

    async def delete_by_ids(self, profile_id: UUID, interest_ids: list[UUID]) -> None:
        if interest_ids:
            delete_stmt = delete(self.model).where(
                self.model.profile_id == profile_id,
                self.model.interest_id.in_(interest_ids),
            )
            await self.session.execute(delete_stmt)

    async def delete_by_profile_id(self, profile_id: UUID) -> None:
        stmt = delete(self.model).where(self.model.profile_id == profile_id)
        await self.session.execute(stmt)
