from uuid import UUID

from fastapi import WebSocket

from app.core.logger import app_logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, dict[UUID, WebSocket]] = {}
        self.profile_rooms: dict[UUID, set[UUID]] = {}

    async def connect(
        self, room_id: UUID, profile_id: UUID, websocket: WebSocket, user_id: UUID
    ):
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

        self.active_connections[room_id][profile_id] = websocket

        if profile_id not in self.profile_rooms:
            self.profile_rooms[profile_id] = set()
        self.profile_rooms[profile_id].add(room_id)

        app_logger.info(
            f"WebSocket подключен: user_id={user_id}, profile_id={profile_id}, room_id={room_id}"
        )

    def disconnect(self, room_id: UUID, profile_id: UUID):
        if room_id in self.active_connections:
            if profile_id in self.active_connections[room_id]:
                del self.active_connections[room_id][profile_id]
                app_logger.info(
                    f"WebSocket отключен: profile_id={profile_id}, room_id={room_id}"
                )

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                app_logger.info(f"WebSocket: комната {room_id} стала пустой")

        if profile_id in self.profile_rooms:
            self.profile_rooms[profile_id].discard(room_id)
            if not self.profile_rooms[profile_id]:
                del self.profile_rooms[profile_id]
                app_logger.info(
                    f"WebSocket: у профиля {profile_id} больше нет активных комнат"
                )

    def disconnect_all(self, profile_id: UUID):
        if profile_id in self.profile_rooms:
            room_ids = list(self.profile_rooms[profile_id])
            app_logger.info(
                f"WebSocket: отключаем профиль {profile_id} от комнат: {room_ids}"
            )
            for room_id in room_ids:
                self.disconnect(room_id, profile_id)

    async def send_personal_message(
        self, message: dict, room_id: UUID, profile_id: UUID
    ):
        if room_id in self.active_connections:
            if profile_id in self.active_connections[room_id]:
                websocket = self.active_connections[room_id][profile_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    app_logger.error(
                        f"Ошибка отправки личного сообщения профилю {profile_id}: {e}"
                    )

    async def broadcast(
        self, message: dict, room_id: UUID, exclude_profile_id: UUID = None
    ):
        if room_id in self.active_connections:
            app_logger.debug(
                f"WebSocket: рассылка в комнату {room_id}, исключая {exclude_profile_id}"
            )

            disconnected_profiles = []

            for pid, websocket in self.active_connections[room_id].items():
                if pid == exclude_profile_id:
                    continue

                try:
                    await websocket.send_json(message)
                except Exception as e:
                    app_logger.error(f"Ошибка отправки сообщения профилю {pid}: {e}")
                    disconnected_profiles.append(pid)

            for pid in disconnected_profiles:
                self.disconnect(room_id, pid)

    def get_room_participants(self, room_id: UUID) -> list[UUID]:
        if room_id in self.active_connections:
            return list(self.active_connections[room_id].keys())
        return []

    def is_profile_connected(self, room_id: UUID, profile_id: UUID) -> bool:
        return (
            room_id in self.active_connections
            and profile_id in self.active_connections[room_id]
        )

    def get_profile_rooms(self, profile_id: UUID) -> list[UUID]:
        if profile_id in self.profile_rooms:
            return list(self.profile_rooms[profile_id])
        return []

    def get_room_online_count(self, room_id: UUID) -> int:
        if room_id in self.active_connections:
            return len(self.active_connections[room_id])
        return 0


connection_manager = ConnectionManager()
