import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from app.api.websockets.room_connection_manager import room_connection_manager
from app.core.logger import app_logger
from app.core.websocket.room_events import RoomEventType, RoomWebSocketMessage
from app.db.unit_of_work import UnitOfWork
from app.schemas.room_message import RoomMessageCreate
from app.services.room import RoomService
from app.services.websocket.room import WebSocketRoomService


class RoomWebSocketHandler:
    def __init__(self, room_id: UUID, profile_id: UUID):
        self.room_id = room_id
        self.profile_id = profile_id

    async def handle_message(self, data: dict[str, Any]) -> RoomWebSocketMessage:
        message_type = data.get("type")

        if message_type == "send_message":
            return await self._handle_send_message(data)
        elif message_type == "typing_started":
            return await self._handle_typing_started()
        elif message_type == "typing_stopped":
            return await self._handle_typing_stopped()
        elif message_type == "ping":
            return await self._handle_ping()
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    async def _handle_send_message(self, data: dict[str, Any]) -> RoomWebSocketMessage:
        content = data.get("content")
        parent_message_id = data.get("parent_message_id")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        if len(content) > 5000:
            raise ValueError("Message is too long (maximum 5000 characters)")

        async with UnitOfWork() as uow:
            wrs = WebSocketRoomService()
            room_service = RoomService(UnitOfWork(), wrs)

            participant = await uow.room_participant.get_participant(
                self.room_id, self.profile_id
            )
            if not participant:
                raise ValueError("You are not a participant of this room")

            if participant.is_banned:
                raise ValueError("You are banned in this room")

            if participant.is_muted:
                raise ValueError("You are muted in this room")

            message_create_data = {"content": content.strip()}
            if parent_message_id:
                try:
                    message_create_data["parent_message_id"] = UUID(parent_message_id)
                except ValueError:
                    raise ValueError("Invalid parent_message_id format")

            message_create = RoomMessageCreate(**message_create_data)

            message = await room_service.send_message(
                room_id=self.room_id,
                message_create=message_create,
                profile_id=self.profile_id,
            )

            app_logger.info(
                f"Сообщение отправлено в комнату {self.room_id} от профиля {self.profile_id}"
            )

            return RoomWebSocketMessage(
                type=RoomEventType.MESSAGE_SENT,
                data={
                    "message": {
                        "id": str(message.id),
                        "room_id": str(message.room_id),
                        "sender_id": str(message.sender_id),
                        "content": message.content,
                        "parent_message_id": (
                            str(message.parent_message_id)
                            if message.parent_message_id
                            else None
                        ),
                        "created_at": message.created_at.isoformat(),
                        "updated_at": message.updated_at.isoformat(),
                        "is_edited": message.is_edited,
                        "is_deleted": message.is_deleted,
                    },
                    "sender_profile_id": str(self.profile_id),
                },
                timestamp=datetime.now(timezone.utc),
                room_id=self.room_id,
                sender_profile_id=self.profile_id,
            )

    async def _handle_typing_started(self) -> RoomWebSocketMessage:
        app_logger.debug(
            f"Профиль {self.profile_id} начал печатать в комнате {self.room_id}"
        )

        return RoomWebSocketMessage(
            type=RoomEventType.TYPING_STARTED,
            data={"profile_id": str(self.profile_id), "room_id": str(self.room_id)},
            timestamp=datetime.now(timezone.utc),
            room_id=self.room_id,
            sender_profile_id=self.profile_id,
        )

    async def _handle_typing_stopped(self) -> RoomWebSocketMessage:
        app_logger.debug(
            f"Профиль {self.profile_id} закончил печатать в комнате {self.room_id}"
        )

        return RoomWebSocketMessage(
            type=RoomEventType.TYPING_STOPPED,
            data={"profile_id": str(self.profile_id), "room_id": str(self.room_id)},
            timestamp=datetime.now(timezone.utc),
            room_id=self.room_id,
            sender_profile_id=self.profile_id,
        )

    async def _handle_ping(self) -> RoomWebSocketMessage:
        return RoomWebSocketMessage(
            type=RoomEventType.PONG,
            data={"timestamp": datetime.now(timezone.utc).isoformat()},
            timestamp=datetime.now(timezone.utc),
        )

    async def create_connection_event(self) -> RoomWebSocketMessage:
        return RoomWebSocketMessage(
            type=RoomEventType.CONNECTION_ESTABLISHED,
            data={
                "profile_id": str(self.profile_id),
                "room_id": str(self.room_id),
                "online_count": room_connection_manager.get_room_online_count(
                    self.room_id
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=self.room_id,
            sender_profile_id=self.profile_id,
        )
