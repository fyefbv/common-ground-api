from uuid import UUID

from fastapi import WebSocket

from app.core.logger import app_logger


class ChatRouletteConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, dict[UUID, WebSocket]] = {}
        self.profile_sessions: dict[UUID, UUID] = {}

    async def connect(self, session_id: UUID, profile_id: UUID, websocket: WebSocket):
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}

        self.active_connections[session_id][profile_id] = websocket

        self.profile_sessions[profile_id] = session_id

        app_logger.info(
            f"WebSocket подключен к чат-рулетке: profile_id={profile_id}, session_id={session_id}"
        )

    def disconnect(self, session_id: UUID, profile_id: UUID):
        if session_id in self.active_connections:
            if profile_id in self.active_connections[session_id]:
                del self.active_connections[session_id][profile_id]
                app_logger.info(
                    f"WebSocket отключен от чат-рулетки: profile_id={profile_id}, session_id={session_id}"
                )

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                app_logger.info(
                    f"WebSocket: сессия чат-рулетки {session_id} стала пустой"
                )

        if profile_id in self.profile_sessions:
            del self.profile_sessions[profile_id]
            app_logger.info(
                f"WebSocket: у профиля {profile_id} больше нет активных сессий чат-рулетки"
            )

    async def send_personal_message(
        self, message: dict, session_id: UUID, profile_id: UUID
    ):
        if session_id in self.active_connections:
            if profile_id in self.active_connections[session_id]:
                websocket = self.active_connections[session_id][profile_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    app_logger.error(
                        f"Ошибка отправки личного сообщения профилю {profile_id} в сессии {session_id}: {e}"
                    )

    async def broadcast(
        self, message: dict, session_id: UUID, exclude_profile_id: UUID = None
    ):
        if session_id in self.active_connections:
            app_logger.debug(
                f"WebSocket: рассылка в сессию чат-рулетки {session_id}, исключая {exclude_profile_id}"
            )

            disconnected_profiles = []

            for pid, websocket in self.active_connections[session_id].items():
                if pid == exclude_profile_id:
                    continue

                try:
                    await websocket.send_json(message)
                except Exception as e:
                    app_logger.error(
                        f"Ошибка отправки сообщения профилю {pid} в сессии {session_id}: {e}"
                    )
                    disconnected_profiles.append(pid)

            for pid in disconnected_profiles:
                self.disconnect(session_id, pid)

    def get_partner_profile_id(self, session_id: UUID, profile_id: UUID) -> UUID | None:
        if session_id in self.active_connections:
            participants = self.active_connections[session_id]
            for pid in participants:
                if pid != profile_id:
                    return pid
        return None

    def get_session_participants(self, session_id: UUID) -> list[UUID]:
        if session_id in self.active_connections:
            return list(self.active_connections[session_id].keys())
        return []


roulette_connection_manager = ChatRouletteConnectionManager()
