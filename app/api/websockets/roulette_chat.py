import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.websockets.roulette_connection_manager import roulette_connection_manager
from app.api.websockets.roulette_handlers import ChatRouletteWebSocketHandler
from app.core.logger import app_logger
from app.core.websocket.auth import authenticate_websocket
from app.core.websocket.chat_roulette_events import (
    ChatRouletteEventType,
    ChatRouletteWebSocketMessage,
)
from app.db.unit_of_work import UnitOfWork
from app.services.chat_roulette import ChatRouletteService
from app.services.websocket.chat_roulette import WebSocketChatRouletteService
from app.utils.object_storage import ObjectStorageService

ws_chat_roulette_router = APIRouter()


async def validate_session_access(session_id: UUID, profile_id: UUID) -> bool:
    try:
        async with UnitOfWork() as uow:
            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )

            if not session:
                app_logger.warning(
                    f"У профиля {profile_id} нет активных сессий чат-рулетки"
                )
                return False

            if session.id != session_id:
                app_logger.warning(
                    f"Профиль {profile_id} пытается подключиться к не своей сессии {session_id}"
                )
                return False

            if session.profile1_id != profile_id and session.profile2_id != profile_id:
                app_logger.warning(
                    f"Профиль {profile_id} не является участником сессии {session_id}"
                )
                return False

            return True

    except Exception as e:
        app_logger.error(f"Ошибка проверки доступа к сессии чат-рулетки: {e}")
        return False


@ws_chat_roulette_router.websocket("/chat-roulette/{session_id}")
async def websocket_roulette_chat(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(...),
):
    app_logger.info(f"Попытка подключения WebSocket к сессии чат-рулетки {session_id}")

    auth_result = await authenticate_websocket(websocket, token)
    if not auth_result:
        return

    _, profile_id = auth_result

    has_access = await validate_session_access(session_id, profile_id)
    if not has_access:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="No access to the session"
        )
        return

    handler = ChatRouletteWebSocketHandler(session_id, profile_id)

    try:
        await roulette_connection_manager.connect(session_id, profile_id, websocket)

        connection_event = await handler.create_connection_event()
        await roulette_connection_manager.send_personal_message(
            connection_event.to_dict(), session_id, profile_id
        )

        partner_profile_id = roulette_connection_manager.get_partner_profile_id(
            session_id, profile_id
        )

        if partner_profile_id:
            partner_connected_event = ChatRouletteWebSocketMessage(
                type=ChatRouletteEventType.PARTNER_CONNECTED,
                data={
                    "partner_profile_id": str(partner_profile_id),
                    "session_id": str(session_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                sender_profile_id=profile_id,
            )
            await roulette_connection_manager.send_personal_message(
                partner_connected_event.to_dict(), session_id, profile_id
            )

        app_logger.info(
            f"Профиль {profile_id} присоединился к сессии чат-рулетки {session_id} через WebSocket"
        )

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=300)
            except asyncio.TimeoutError:
                ping_event = ChatRouletteWebSocketMessage(
                    type=ChatRouletteEventType.PING,
                    data={"timestamp": datetime.now(timezone.utc).isoformat()},
                    timestamp=datetime.now(timezone.utc),
                )
                await roulette_connection_manager.send_personal_message(
                    ping_event.to_dict(), session_id, profile_id
                )
                continue
            except WebSocketDisconnect:
                app_logger.info(
                    f"WebSocket отключен: профиль={profile_id}, сессия={session_id}"
                )

                partner_profile_id = roulette_connection_manager.get_partner_profile_id(
                    session_id, profile_id
                )

                if partner_profile_id:
                    partner_disconnected_event = ChatRouletteWebSocketMessage(
                        type=ChatRouletteEventType.PARTNER_DISCONNECTED,
                        data={
                            "partner_profile_id": str(partner_profile_id),
                            "session_id": str(session_id),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        timestamp=datetime.now(timezone.utc),
                        session_id=session_id,
                        sender_profile_id=profile_id,
                    )
                    await roulette_connection_manager.send_personal_message(
                        partner_disconnected_event.to_dict(),
                        session_id,
                        partner_profile_id,
                    )

                roulette_connection_manager.disconnect(session_id, profile_id)
                break
            except Exception as e:
                app_logger.error(f"Ошибка получения сообщения WebSocket: {e}")
                roulette_connection_manager.disconnect(session_id, profile_id)
                break

            try:
                response_event = await handler.handle_message(data)

                if response_event.type == ChatRouletteEventType.PONG:
                    await roulette_connection_manager.send_personal_message(
                        response_event.to_dict(), session_id, profile_id
                    )

            except ValueError as e:
                app_logger.warning(f"Ошибка валидации WebSocket сообщения: {e}")
                error_event = ChatRouletteWebSocketMessage(
                    type=ChatRouletteEventType.ERROR,
                    data={"message": str(e)},
                    timestamp=datetime.now(timezone.utc),
                )
                await roulette_connection_manager.send_personal_message(
                    error_event.to_dict(), session_id, profile_id
                )

            except Exception as e:
                app_logger.error(f"Ошибка обработки WebSocket сообщения: {e}")
                error_event = ChatRouletteWebSocketMessage(
                    type=ChatRouletteEventType.ERROR,
                    data={"message": "Internal server error"},
                    timestamp=datetime.now(timezone.utc),
                )
                await roulette_connection_manager.send_personal_message(
                    error_event.to_dict(), session_id, profile_id
                )

    except WebSocketDisconnect:
        app_logger.info(
            f"WebSocket отключен: профиль={profile_id}, сессия={session_id}"
        )

        partner_profile_id = roulette_connection_manager.get_partner_profile_id(
            session_id, profile_id
        )

        if partner_profile_id:
            partner_disconnected_event = ChatRouletteWebSocketMessage(
                type=ChatRouletteEventType.PARTNER_DISCONNECTED,
                data={
                    "partner_profile_id": str(partner_profile_id),
                    "session_id": str(session_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                sender_profile_id=profile_id,
            )
            await roulette_connection_manager.send_personal_message(
                partner_disconnected_event.to_dict(), session_id, partner_profile_id
            )

        roulette_connection_manager.disconnect(session_id, profile_id)

    except Exception as e:
        app_logger.error(f"Непредвиденная ошибка WebSocket: {e}")
        roulette_connection_manager.disconnect(session_id, profile_id)
