import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from app.api.websockets.roulette_connection_manager import roulette_connection_manager
from app.core.config import settings
from app.core.logger import app_logger
from app.core.websocket.chat_roulette_events import (
    ChatRouletteEventType,
    ChatRouletteWebSocketMessage,
)
from app.db.unit_of_work import UnitOfWork
from app.schemas.chat_roulette import ChatRouletteMessageCreate
from app.services.chat_roulette import ChatRouletteService
from app.services.websocket.chat_roulette import WebSocketChatRouletteService
from app.utils.object_storage import ObjectStorageService


class ChatRouletteWebSocketHandler:
    def __init__(self, session_id: UUID, profile_id: UUID):
        self.session_id = session_id
        self.profile_id = profile_id

    async def handle_message(
        self, data: dict[str, Any]
    ) -> ChatRouletteWebSocketMessage:
        message_type = data.get("type")

        if message_type == "send_message":
            return await self._handle_send_message(data)
        elif message_type == "ping":
            return await self._handle_ping()
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    async def _handle_send_message(
        self, data: dict[str, Any]
    ) -> ChatRouletteWebSocketMessage:
        content = data.get("content")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        if len(content) > 5000:
            raise ValueError("Message is too long (maximum 5000 characters)")

        async with UnitOfWork() as uow:
            oss = ObjectStorageService(
                endpoint_url=settings.S3_ENDPOINT_URL,
                access_key_id=settings.S3_ACCESS_KEY_ID,
                secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                bucket_name=settings.S3_BUCKET_NAME,
            )
            wcrs = WebSocketChatRouletteService()
            chat_roulette_service = ChatRouletteService(UnitOfWork(), oss, wcrs)

            session = await uow.chat_roulette_session.find_active_session_by_profile(
                self.profile_id
            )
            if not session:
                raise ValueError("You don't have an active session")

            if session.id != self.session_id:
                raise ValueError("Invalid session ID")

            partner_profile_id = (
                session.profile2_id
                if session.profile1_id == self.profile_id
                else session.profile1_id
            )
            if not partner_profile_id:
                raise ValueError("Partner not found in session")

            message = await chat_roulette_service.send_message(self.profile_id, content)

            app_logger.info(
                f"Сообщение отправлено в сессию чат-рулетки {self.session_id} от профиля {self.profile_id}"
            )

            return ChatRouletteWebSocketMessage(
                type=ChatRouletteEventType.MESSAGE_SENT,
                data={
                    "message": {
                        "id": str(message.session_id),
                        "sender_id": str(self.profile_id),
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                    },
                    "sender_profile_id": str(self.profile_id),
                },
                timestamp=datetime.now(timezone.utc),
                session_id=self.session_id,
                sender_profile_id=self.profile_id,
            )

    async def _handle_ping(self) -> ChatRouletteWebSocketMessage:
        return ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.PONG,
            data={"timestamp": datetime.now(timezone.utc).isoformat()},
            timestamp=datetime.now(timezone.utc),
        )

    async def create_connection_event(self) -> ChatRouletteWebSocketMessage:
        return ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.CONNECTION_ESTABLISHED,
            data={
                "profile_id": str(self.profile_id),
                "session_id": str(self.session_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            timestamp=datetime.now(timezone.utc),
            session_id=self.session_id,
            sender_profile_id=self.profile_id,
        )
