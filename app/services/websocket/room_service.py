from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.api.websockets.connection_manager import connection_manager
from app.core.logger import app_logger
from app.core.websocket.events import WebSocketEventType, WebSocketMessage


class WebSocketRoomService:
    def __init__(self):
        pass

    async def broadcast_new_message(
        self, room_id: UUID, message_data: dict[str, Any], sender_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.MESSAGE_SENT,
            data={"message": message_data, "sender_profile_id": str(sender_profile_id)},
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=sender_profile_id,
        )

        await connection_manager.broadcast(event.to_dict(), room_id)
        app_logger.info(f"Новое сообщение разослано в комнату {room_id}")

    async def broadcast_room_update(
        self,
        room_id: UUID,
        update_data: dict[str, Any],
        updater_profile_id: UUID = None,
    ):
        event_data = {"room": update_data}
        if updater_profile_id:
            event_data["updater_profile_id"] = str(updater_profile_id)

        event = WebSocketMessage(
            type=WebSocketEventType.ROOM_UPDATED,
            data=event_data,
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=updater_profile_id,
        )

        await connection_manager.broadcast(
            event.to_dict(), room_id, exclude_profile_id=updater_profile_id
        )
        app_logger.info(f"Обновление комнаты {room_id} разослано через WebSocket")

    async def broadcast_room_deleted(
        self, room_id: UUID, deleter_profile_id: UUID = None
    ):
        participants = connection_manager.get_room_participants(room_id)

        event_data = {"room_id": str(room_id)}
        if deleter_profile_id:
            event_data["deleter_profile_id"] = str(deleter_profile_id)

        event = WebSocketMessage(
            type=WebSocketEventType.ROOM_DELETED,
            data=event_data,
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=deleter_profile_id,
        )

        for profile_id in participants:
            await connection_manager.send_personal_message(
                event.to_dict(), room_id, profile_id
            )

        for profile_id in participants:
            connection_manager.disconnect(room_id, profile_id)

        app_logger.info(f"Удаление комнаты {room_id} разослано через WebSocket")

    async def broadcast_participant_muted(
        self, room_id: UUID, muted_profile_id: UUID, muter_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_MUTED,
            data={
                "muted_profile_id": str(muted_profile_id),
                "muter_profile_id": str(muter_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=muter_profile_id,
        )

        await connection_manager.broadcast(event.to_dict(), room_id)

        app_logger.info(f"Участник {muted_profile_id} замьючен в комнате {room_id}")

    async def broadcast_participant_unmuted(
        self, room_id: UUID, unmuted_profile_id: UUID, unmuter_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_UNMUTED,
            data={
                "unmuted_profile_id": str(unmuted_profile_id),
                "unmuter_profile_id": str(unmuter_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=unmuter_profile_id,
        )

        await connection_manager.broadcast(event.to_dict(), room_id)

        app_logger.info(f"Участник {unmuted_profile_id} размьючен в комнате {room_id}")

    async def broadcast_participant_banned(
        self, room_id: UUID, banned_profile_id: UUID, banner_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_BANNED,
            data={
                "banned_profile_id": str(banned_profile_id),
                "banner_profile_id": str(banner_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=banner_profile_id,
        )

        await connection_manager.broadcast(
            event.to_dict(), room_id, exclude_profile_id=banned_profile_id
        )

        personal_event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_BANNED,
            data={
                "banned_profile_id": str(banned_profile_id),
                "room_id": str(room_id),
                "reason": "You have been banned from this room",
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=banner_profile_id,
        )
        await connection_manager.send_personal_message(
            personal_event.to_dict(), room_id, banned_profile_id
        )

        if connection_manager.is_profile_connected(room_id, banned_profile_id):
            connection_manager.disconnect(room_id, banned_profile_id)

        app_logger.info(f"Участник {banned_profile_id} забанен в комнате {room_id}")

    async def broadcast_participant_unbanned(
        self, room_id: UUID, unbanned_profile_id: UUID, unbanner_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_UNBANNED,
            data={
                "unbanned_profile_id": str(unbanned_profile_id),
                "unbanner_profile_id": str(unbanner_profile_id),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=unbanner_profile_id,
        )

        await connection_manager.broadcast(event.to_dict(), room_id)

        app_logger.info(f"Участник {unbanned_profile_id} разбанен в комнате {room_id}")

    async def broadcast_participant_kicked(
        self, room_id: UUID, kicked_profile_id: UUID, kicker_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_KICKED,
            data={
                "profile_id": str(kicked_profile_id),
                "kicker_profile_id": str(kicker_profile_id),
                "is_kicked": True,
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=kicker_profile_id,
        )

        await connection_manager.broadcast(
            event.to_dict(), room_id, exclude_profile_id=kicker_profile_id
        )

        if connection_manager.is_profile_connected(room_id, kicked_profile_id):
            connection_manager.disconnect(room_id, kicked_profile_id)

        app_logger.info(f"Участник {kicked_profile_id} кикнут из комнаты {room_id}")

    async def broadcast_participant_joined(
        self, room_id: UUID, joined_profile_id: UUID
    ):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_JOINED,
            data={
                "profile_id": str(joined_profile_id),
                "joined_at": datetime.now(timezone.utc).isoformat(),
                "online_count": connection_manager.get_room_online_count(room_id),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=joined_profile_id,
        )

        await connection_manager.broadcast(
            event.to_dict(), room_id, exclude_profile_id=joined_profile_id
        )
        app_logger.info(
            f"Участник {joined_profile_id} присоединился к комнате {room_id}"
        )

    async def broadcast_participant_left(self, room_id: UUID, left_profile_id: UUID):
        event = WebSocketMessage(
            type=WebSocketEventType.PARTICIPANT_LEFT,
            data={
                "profile_id": str(left_profile_id),
                "left_at": datetime.now(timezone.utc).isoformat(),
                "online_count": connection_manager.get_room_online_count(room_id),
            },
            timestamp=datetime.now(timezone.utc),
            room_id=room_id,
            sender_profile_id=left_profile_id,
        )

        await connection_manager.broadcast(
            event.to_dict(), room_id, exclude_profile_id=left_profile_id
        )
        app_logger.info(f"Участник {left_profile_id} вышел из комнаты {room_id}")

    def get_online_participants(self, room_id: UUID) -> list[UUID]:
        return connection_manager.get_room_participants(room_id)

    def is_profile_online(self, room_id: UUID, profile_id: UUID) -> bool:
        return connection_manager.is_profile_connected(room_id, profile_id)

    def get_online_count(self, room_id: UUID) -> int:
        return connection_manager.get_room_online_count(room_id)
