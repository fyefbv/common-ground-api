from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.room_message import RoomMessage
from app.db.models.room_participant import RoomParticipant, RoomParticipantRole
from app.repositories.base import Repository


class RoomParticipantRepository(Repository):
    model = RoomParticipant

    async def add_participant(
        self,
        room_id: UUID,
        profile_id: UUID,
        role: RoomParticipantRole = RoomParticipantRole.MEMBER,
    ) -> RoomParticipant:
        participant_data = {
            "room_id": room_id,
            "profile_id": profile_id,
            "role": role,
            "joined_at": datetime.now(timezone.utc),
        }
        return await self.add_one(participant_data)

    async def get_participant(
        self, room_id: UUID, profile_id: UUID
    ) -> RoomParticipant | None:
        stmt = select(self.model).where(
            and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_room_participants(
        self,
        room_id: UUID,
        include_banned: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RoomParticipant]:
        stmt = select(self.model).where(self.model.room_id == room_id)

        if not include_banned:
            stmt = stmt.where(self.model.is_banned == False)

        stmt = (
            stmt.order_by(desc(self.model.is_online), desc(self.model.joined_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_online_participants(self, room_id: UUID) -> list[RoomParticipant]:
        stmt = select(self.model).where(
            and_(
                self.model.room_id == room_id,
                self.model.is_online == True,
                self.model.is_banned == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def set_online_status(
        self, room_id: UUID, profile_id: UUID, is_online: bool
    ) -> None:
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
            )
            .values(is_online=is_online)
        )
        await self.session.execute(stmt)

    async def update_role(
        self, room_id: UUID, profile_id: UUID, role: RoomParticipantRole
    ) -> None:
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
            )
            .values(role=role)
        )
        await self.session.execute(stmt)

    async def remove_participant(self, room_id: UUID, profile_id: UUID) -> bool:
        stmt = delete(self.model).where(
            and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def ban_participant(self, room_id: UUID, profile_id: UUID) -> None:
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
            )
            .values(is_banned=True)
        )
        await self.session.execute(stmt)

    async def unban_participant(self, room_id: UUID, profile_id: UUID) -> None:
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
            )
            .values(is_banned=False)
        )
        await self.session.execute(stmt)

    async def mute_participant(self, room_id: UUID, profile_id: UUID) -> None:
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
            )
            .values(is_muted=True)
        )
        await self.session.execute(stmt)

    async def unmute_participant(self, room_id: UUID, profile_id: UUID) -> None:
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                and_(self.model.room_id == room_id, self.model.profile_id == profile_id)
            )
            .values(is_muted=False)
        )
        await self.session.execute(stmt)

    async def get_room_counts(self, room_id: UUID) -> tuple[int, int]:
        from sqlalchemy import func, select

        participants_stmt = (
            select(func.count())
            .select_from(RoomParticipant)
            .where(
                RoomParticipant.room_id == room_id, RoomParticipant.is_banned == False
            )
        )
        participants_result = await self.session.execute(participants_stmt)
        participants_count = participants_result.scalar() or 0

        messages_stmt = (
            select(func.count())
            .select_from(RoomMessage)
            .where(RoomMessage.room_id == room_id, RoomMessage.is_deleted == False)
        )
        messages_result = await self.session.execute(messages_stmt)
        messages_count = messages_result.scalar() or 0

        return participants_count, messages_count
