from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, delete, desc, select, update

from app.db.models.chat_roulette_search import ChatRouletteSearch
from app.repositories.base import Repository


class ChatRouletteSearchRepository(Repository):
    model = ChatRouletteSearch

    async def find_active_search(self, profile_id: UUID) -> ChatRouletteSearch | None:
        stmt = select(self.model).where(
            self.model.profile_id == profile_id, self.model.is_active == True
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_search(
        self,
        profile_id: UUID,
        priority_interest_ids: list[UUID] | None = None,
        max_wait_time_minutes: int = 10,
    ) -> ChatRouletteSearch:
        existing_search = await self.find_active_search(profile_id)

        if existing_search:
            update_data = {
                "priority_interest_ids": priority_interest_ids,
                "max_wait_time_minutes": max_wait_time_minutes,
                "search_started_at": datetime.now(timezone.utc),
            }

            await self.update(existing_search.id, update_data)
            return await self.get_by_id(existing_search.id)
        else:
            search_data = {
                "profile_id": profile_id,
                "priority_interest_ids": priority_interest_ids,
                "max_wait_time_minutes": max_wait_time_minutes,
                "search_started_at": datetime.now(timezone.utc),
                "is_active": True,
            }

            return await self.add_one(search_data)

    async def deactivate_search(self, profile_id: UUID) -> bool:
        stmt = (
            update(self.model)
            .where(self.model.profile_id == profile_id, self.model.is_active == True)
            .values(is_active=False)
        )

        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def deactivate_search_by_id(self, search_id: UUID) -> bool:
        stmt = (
            update(self.model)
            .where(self.model.id == search_id, self.model.is_active == True)
            .values(is_active=False)
        )

        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def cleanup_old_searches(self, hours: int = 24) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = delete(self.model).where(self.model.search_started_at < cutoff)

        result = await self.session.execute(stmt)
        return result.rowcount

    async def increase_search_score(self, search_id: UUID, increment: int = 1) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == search_id)
            .values(search_score=self.model.search_score + increment)
        )

        await self.session.execute(stmt)

    async def get_active_searches_count(self) -> int:
        stmt = select(self.model).where(self.model.is_active == True)

        result = await self.session.execute(stmt)
        searches = result.scalars().all()
        return len(searches)
