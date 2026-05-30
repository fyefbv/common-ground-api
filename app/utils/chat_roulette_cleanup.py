import asyncio
from datetime import datetime, timezone

from app.core.logger import app_logger
from app.db.models.chat_roulette_session import ChatRouletteSessionStatus
from app.db.unit_of_work import UnitOfWork
from app.services.websocket.chat_roulette import WebSocketChatRouletteService


async def run_session_cleanup():
    """
    Фоновая задача для автоматической очистки просроченных сессий чат-рулетки.

    Регулярно проверяет сессии на истечение срока действия.
    Завершает просроченные сессии, обновляет их статус на COMPLETED
    и уведомляет участников через WebSocket.
    """
    wcrs = WebSocketChatRouletteService()

    try:
        while True:
            try:
                async with UnitOfWork() as uow:
                    expired_sessions = (
                        await uow.chat_roulette_session.get_expired_sessions()
                    )

                    if expired_sessions:
                        for session in expired_sessions:
                            await uow.chat_roulette_session.update_session_status(
                                session.id,
                                ChatRouletteSessionStatus.COMPLETED,
                                "Session expired automatically",
                            )

                        await uow.commit()
                        app_logger.info(
                            f"Автоматически завершено {len(expired_sessions)} просроченных сессий"
                        )

                        for session in expired_sessions:
                            try:
                                await wcrs.broadcast_session_ended(
                                    session.id,
                                    session.profile1_id,
                                    "Session expired automatically",
                                )
                            except Exception as e:
                                app_logger.error(
                                    f"Ошибка при отправке WebSocket уведомления о завершении сессии {session.id}: {e}"
                                )

                    expiring_soon = (
                        await uow.chat_roulette_session.get_expiring_sessions(
                            minutes_before=2
                        )
                    )
                    if expiring_soon:
                        next_expiry = min(s.expires_at for s in expiring_soon)
                        sleep_time = max(
                            0,
                            (next_expiry - datetime.now(timezone.utc)).total_seconds(),
                        )
                    else:
                        sleep_time = 60.0

                await asyncio.sleep(min(sleep_time, 120.0))

            except Exception as e:
                app_logger.error(f"Ошибка очистки сессий в фоне: {e}")
                await asyncio.sleep(60.0)

    except asyncio.CancelledError:
        app_logger.info("Задача очистки сессий чат-рулетки отменена")
        raise
