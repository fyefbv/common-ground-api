from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.room import Room
from app.db.models.room_participant import RoomParticipant
from app.repositories.base import Repository


class RoomRepository(Repository):
    model = Room

    async def find_by_name(self, name: str) -> Room | None:
        stmt = select(self.model).where(self.model.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_rooms(
        self,
        query: str | None = None,
        interest_id: UUID | None = None,
        tags: list[str] | None = None,
        creator_id: UUID | None = None,
        is_private: bool | None = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Room]:
        stmt = select(self.model)

        if query:
            stmt = stmt.where(
                or_(
                    self.model.name.ilike(f"%{query}%"),
                    self.model.description.ilike(f"%{query}%"),
                )
            )

        if interest_id:
            stmt = stmt.where(self.model.primary_interest_id == interest_id)

        if tags:
            for tag in tags:
                stmt = stmt.where(self.model.tags.contains([tag]))

        if creator_id:
            stmt = stmt.where(self.model.creator_id == creator_id)

        if is_private is not None:
            stmt = stmt.where(self.model.is_private == is_private)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_popular_rooms(self, limit: int = 20) -> list[Room]:
        participants_subq = (
            select(RoomParticipant.room_id, func.count().label("participants_count"))
            .where(RoomParticipant.is_banned == False)
            .group_by(RoomParticipant.room_id)
            .subquery()
        )

        stmt = (
            select(self.model)
            .outerjoin(participants_subq, participants_subq.c.room_id == self.model.id)
            .where(self.model.is_private == False)
            .order_by(
                desc(func.coalesce(participants_subq.c.participants_count, 0)),
                desc(self.model.created_at),
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_rooms(self, profile_id: UUID) -> list[Room]:
        stmt = (
            select(self.model)
            .join(RoomParticipant, RoomParticipant.room_id == self.model.id)
            .where(
                RoomParticipant.profile_id == profile_id,
                RoomParticipant.is_banned == False,
            )
            .order_by(self.model.last_activity_at.desc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
