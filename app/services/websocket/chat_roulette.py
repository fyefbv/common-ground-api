from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.api.websockets.roulette_connection_manager import roulette_connection_manager
from app.core.logger import app_logger
from app.core.websocket.chat_roulette_events import (
    ChatRouletteEventType,
    ChatRouletteWebSocketMessage,
)


class WebSocketChatRouletteService:
    def __init__(self):
        pass

    async def broadcast_message_sent(
        self, session_id: UUID, message_data: dict[str, Any], sender_profile_id: UUID
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.MESSAGE_SENT,
            data={"message": message_data, "sender_profile_id": str(sender_profile_id)},
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=sender_profile_id,
        )

        await roulette_connection_manager.broadcast(event.to_dict(), session_id)
        app_logger.info(f"Новое сообщение разослано в сессию чат-рулетки {session_id}")

    async def broadcast_session_extended(
        self,
        session_id: UUID,
        profile_id: UUID,
        extended_minutes: int,
        new_expires_at: datetime,
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.SESSION_EXTENDED,
            data={
                "session_id": str(session_id),
                "profile_id": str(profile_id),
                "extended_minutes": extended_minutes,
                "new_expires_at": new_expires_at.isoformat(),
            },
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=profile_id,
        )

        await roulette_connection_manager.broadcast(event.to_dict(), session_id)
        app_logger.info(f"Продление сессии {session_id} разослано через WebSocket")

    async def broadcast_session_ended(
        self, session_id: UUID, profile_id: UUID, reason: str
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.SESSION_ENDED,
            data={
                "session_id": str(session_id),
                "profile_id": str(profile_id),
                "reason": reason,
            },
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=profile_id,
        )

        await roulette_connection_manager.broadcast(event.to_dict(), session_id)

        participants = roulette_connection_manager.get_session_participants(session_id)
        for participant_id in participants:
            roulette_connection_manager.disconnect(session_id, participant_id)

        app_logger.info(f"Завершение сессии {session_id} разослано через WebSocket")

    async def broadcast_extension_request(
        self, session_id: UUID, requesting_profile_id: UUID, partner_profile_id: UUID
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.EXTENSION_REQUESTED,
            data={
                "session_id": str(session_id),
                "requesting_profile_id": str(requesting_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=requesting_profile_id,
        )

        await roulette_connection_manager.broadcast(event.to_dict(), session_id)
        app_logger.info(
            f"Запрос на продление сессии {session_id} отправлен партнеру {partner_profile_id}"
        )

    async def broadcast_extension_approved(
        self, session_id: UUID, approving_profile_id: UUID, partner_profile_id: UUID
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.EXTENSION_APPROVED,
            data={
                "session_id": str(session_id),
                "approving_profile_id": str(approving_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=approving_profile_id,
        )

        await roulette_connection_manager.broadcast(event.to_dict(), session_id)
        app_logger.info(
            f"Подтверждение продления сессии {session_id} отправлено партнеру {partner_profile_id}"
        )

    async def broadcast_extension_rejected(
        self, session_id: UUID, rejecting_profile_id: UUID, requesting_profile_id: UUID
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.EXTENSION_REJECTED,
            data={
                "session_id": str(session_id),
                "rejecting_profile_id": str(rejecting_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=rejecting_profile_id,
        )
        await roulette_connection_manager.broadcast(event.to_dict(), session_id)
        app_logger.info(
            f"Отказ в продлении сессии {session_id} отправлен инициатору {requesting_profile_id}"
        )

    async def broadcast_extension_cancelled(
        self, session_id: UUID, cancelling_profile_id: UUID, partner_profile_id: UUID
    ):
        event = ChatRouletteWebSocketMessage(
            type=ChatRouletteEventType.EXTENSION_CANCELLED,
            data={
                "session_id": str(session_id),
                "cancelling_profile_id": str(cancelling_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            sender_profile_id=cancelling_profile_id,
        )
        await roulette_connection_manager.broadcast(event.to_dict(), session_id)
        app_logger.info(
            f"Отмена запроса на продление сессии {session_id} для партнёра {partner_profile_id}"
        )

    def get_session_participants(self, session_id: UUID) -> list[UUID]:
        return roulette_connection_manager.get_session_participants(session_id)

    def is_profile_connected(self, session_id: UUID, profile_id: UUID) -> bool:
        return roulette_connection_manager.is_profile_connected(session_id, profile_id)
