from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.db.models.chat_roulette_message import ChatRouletteMessage
from app.repositories.base import Repository


class ChatRouletteMessageRepository(Repository):
    model = ChatRouletteMessage

    async def get_messages_by_session(
        self, session_id: UUID, limit: int | None = None, before: datetime | None = None
    ) -> list[ChatRouletteMessage]:
        stmt = select(self.model).where(self.model.session_id == session_id)
        if before:
            stmt = stmt.where(self.model.created_at < before)
        stmt = stmt.order_by(self.model.created_at)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
