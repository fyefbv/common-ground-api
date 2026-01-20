import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_unit_of_work
from app.api.websockets.connection_manager import connection_manager
from app.api.websockets.handlers import WebSocketHandler
from app.core.logger import app_logger
from app.core.websocket.auth import authenticate_websocket
from app.core.websocket.events import WebSocketEventType, WebSocketMessage
from app.db.unit_of_work import UnitOfWork
from app.services.room import RoomService
from app.services.websocket.room_service import WebSocketRoomService

ws_rooms_router = APIRouter()


async def validate_room_access(room_id: UUID, profile_id: UUID) -> bool:
    try:
        async with UnitOfWork() as uow:
            wrs = WebSocketRoomService()
            room_service = RoomService(UnitOfWork(), wrs)

            await room_service.get_room(room_id, profile_id)

            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if not participant:
                app_logger.warning(
                    f"Профиль {profile_id} не является участником комнаты {room_id}"
                )
                return False

            if participant.is_banned:
                app_logger.warning(f"Профиль {profile_id} забанен в комнате {room_id}")
                return False

            return True

    except Exception as e:
        app_logger.error(f"Ошибка проверки доступа к комнате: {e}")
        return False


@ws_rooms_router.websocket("/rooms/{room_id}")
async def websocket_room_chat(
    websocket: WebSocket,
    room_id: UUID,
    token: str = Query(...),
):
    app_logger.info(f"Попытка подключения WebSocket к комнате {room_id}")

    auth_result = await authenticate_websocket(websocket, token)
    if not auth_result:
        return

    user_id, profile_id = auth_result

    has_access = await validate_room_access(room_id, profile_id)
    if not has_access:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="No access to the room"
        )
        return

    handler = WebSocketHandler(room_id, profile_id)

    try:
        await connection_manager.connect(room_id, profile_id, websocket, user_id)

        connection_event = await handler.create_connection_event()
        await connection_manager.send_personal_message(
            connection_event.to_dict(), room_id, profile_id
        )

        app_logger.info(
            f"Профиль {profile_id} присоединился к комнате {room_id} через WebSocket"
        )

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=300)
            except asyncio.TimeoutError:
                ping_event = WebSocketMessage(
                    type=WebSocketEventType.PING,
                    data={"timestamp": datetime.now(timezone.utc).isoformat()},
                    timestamp=datetime.now(timezone.utc),
                )
                await connection_manager.send_personal_message(
                    ping_event.to_dict(), room_id, profile_id
                )
                continue
            except WebSocketDisconnect:
                break
            except Exception as e:
                app_logger.error(f"Ошибка получения сообщения WebSocket: {e}")
                break

            try:
                response_event = await handler.handle_message(data)

                if response_event.type == WebSocketEventType.PONG:
                    await connection_manager.send_personal_message(
                        response_event.to_dict(), room_id, profile_id
                    )
                elif response_event.type in [
                    WebSocketEventType.TYPING_STARTED,
                    WebSocketEventType.TYPING_STOPPED,
                ]:
                    await connection_manager.broadcast(
                        response_event.to_dict(), room_id, exclude_profile_id=profile_id
                    )

            except ValueError as e:
                app_logger.warning(f"Ошибка валидации WebSocket сообщения: {e}")
                error_event = WebSocketMessage(
                    type=WebSocketEventType.ERROR,
                    data={"message": str(e)},
                    timestamp=datetime.now(timezone.utc),
                )
                await connection_manager.send_personal_message(
                    error_event.to_dict(), room_id, profile_id
                )

            except Exception as e:
                app_logger.error(f"Ошибка обработки WebSocket сообщения: {e}")
                error_event = WebSocketMessage(
                    type=WebSocketEventType.ERROR,
                    data={"message": "Internal server error"},
                    timestamp=datetime.now(timezone.utc),
                )
                await connection_manager.send_personal_message(
                    error_event.to_dict(), room_id, profile_id
                )

    except WebSocketDisconnect:
        app_logger.info(f"WebSocket отключен: профиль={profile_id}, комната={room_id}")

        connection_manager.disconnect(room_id, profile_id)

    except Exception as e:
        app_logger.error(f"Непредвиденная ошибка WebSocket: {e}")
        connection_manager.disconnect(room_id, profile_id)
