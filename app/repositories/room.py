from uuid import UUID

from sqlalchemy import func, or_, select

from app.db.models.room import Room
from app.db.models.room_participant import RoomParticipant
from app.repositories.base import Repository


class RoomRepository(Repository):
    model = Room

    async def search_rooms(
        self,
        query: str | None = None,
        interest_ids: list[UUID] | None = None,
        tags: list[str] | None = None,
        participant_id: UUID | None = None,
        only_participant_rooms: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int | None = None,
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

        if interest_ids:
            stmt = stmt.where(self.model.primary_interest_id.in_(interest_ids))

        if tags:
            for tag in tags:
                stmt = stmt.where(self.model.tags.contains([tag]))

        if participant_id is not None:
            participant_room_subq = (
                select(RoomParticipant.room_id)
                .where(
                    RoomParticipant.profile_id == participant_id,
                    RoomParticipant.is_banned == False,
                )
                .subquery()
            )

            if only_participant_rooms:
                stmt = stmt.where(self.model.id.in_(select(participant_room_subq)))
            else:
                stmt = stmt.where(
                    or_(
                        self.model.is_private == False,
                        self.model.id.in_(select(participant_room_subq)),
                    )
                )
        else:
            stmt = stmt.where(self.model.is_private == False)

        if sort_by == "participants":
            participants_subq = (
                select(func.count())
                .where(
                    RoomParticipant.room_id == self.model.id,
                    RoomParticipant.is_banned == False,
                )
                .correlate(self.model)
                .scalar_subquery()
            )
            order_col = participants_subq
        else:
            order_col = self.model.created_at

        if sort_order == "asc":
            stmt = stmt.order_by(order_col.asc())
        else:
            stmt = stmt.order_by(order_col.desc())

        if limit is not None:
            stmt = stmt.limit(limit)

        stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_tags(self, profile_id: UUID) -> list[str]:
        participant_rooms_subq = (
            select(RoomParticipant.room_id)
            .where(
                RoomParticipant.profile_id == profile_id,
                RoomParticipant.is_banned == False,
            )
            .subquery()
        )

        stmt = (
            select(func.unnest(self.model.tags).label("tag"))
            .where(
                or_(
                    self.model.is_private == False,
                    self.model.id.in_(select(participant_rooms_subq)),
                )
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]
