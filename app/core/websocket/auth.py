from typing import Tuple
from uuid import UUID

from fastapi import WebSocket, status

from app.core.auth import decode_jwt
from app.core.exceptions.auth import ExpiredTokenError, InvalidTokenError
from app.core.logger import app_logger


async def authenticate_websocket(
    websocket: WebSocket, token: str
) -> Tuple[UUID, UUID] | None:
    try:
        if not token:
            app_logger.warning("WebSocket: отсутствует токен")
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Token is missing"
            )
            return None

        payload = decode_jwt(token)
        user_id = UUID(payload.get("sub"))
        profile_id_str = payload.get("profile_id")

        if not profile_id_str:
            app_logger.warning(
                f"WebSocket: токен не содержит profile_id для user_id={user_id}"
            )
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Profile not selected",
            )
            return None

        profile_id = UUID(profile_id_str)

        app_logger.info(
            f"WebSocket: успешная аутентификация user_id={user_id}, profile_id={profile_id}"
        )
        return user_id, profile_id

    except (InvalidTokenError, ExpiredTokenError) as e:
        app_logger.error(f"WebSocket: ошибка аутентификации: {e}")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason=str(e.detail)
        )
        return None
    except ValueError as e:
        app_logger.error(f"WebSocket: ошибка формата UUID: {e}")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid UUID format",
        )
        return None
    except Exception as e:
        app_logger.error(f"WebSocket: непредвиденная ошибка аутентификации: {e}")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
        )
        return None
