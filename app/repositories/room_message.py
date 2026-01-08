from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.room_message import RoomMessage
from app.repositories.base import Repository


class RoomMessageRepository(Repository):
    model = RoomMessage

    async def get_room_messages(
        self,
        room_id: UUID,
        before: datetime | None = None,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> list[RoomMessage]:
        stmt = select(self.model).where(self.model.room_id == room_id)

        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        if before:
            stmt = stmt.where(self.model.created_at < before)

        stmt = stmt.order_by(desc(self.model.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        return list(reversed(messages))

    async def get_message_thread(
        self, parent_message_id: UUID, limit: int = 20
    ) -> list[RoomMessage]:
        stmt = (
            select(self.model)
            .where(self.model.parent_message_id == parent_message_id)
            .where(self.model.is_deleted == False)
            .order_by(self.model.created_at)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent_messages(
        self, room_id: UUID, hours: int = 24
    ) -> list[RoomMessage]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.room_id == room_id,
                    self.model.created_at >= cutoff,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.created_at)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def soft_delete_message(self, message_id: UUID) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == message_id)
            .values(is_deleted=True, updated_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def mark_as_edited(self, message_id: UUID) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == message_id)
            .values(is_edited=True, updated_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def get_user_messages_in_room(
        self, room_id: UUID, profile_id: UUID, limit: int = 50
    ) -> list[RoomMessage]:
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.room_id == room_id,
                    self.model.sender_id == profile_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
