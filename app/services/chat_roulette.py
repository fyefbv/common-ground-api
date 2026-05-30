import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.exceptions.chat_roulette import (
    AlreadyInSearchError,
    AlreadyInSessionError,
    AlreadyRatedError,
    CannotRateNonCompletedSessionError,
    CannotRateYourselfError,
    ExtensionNotApprovedError,
    NoActiveSessionError,
    NoMatchingFoundError,
    PartnerNotFoundError,
    SessionAlreadyEndedError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.core.exceptions.profile import ProfileNotFoundError
from app.core.logger import app_logger
from app.db.models.chat_roulette_session import ChatRouletteSessionStatus
from app.db.unit_of_work import UnitOfWork
from app.schemas.chat_roulette import (
    ChatRouletteMessageResponse,
    ChatRouletteRatingRequest,
    ChatRouletteReportRequest,
    ChatRouletteSearchRequest,
    ChatRouletteSearchResponse,
    ChatRouletteSessionResponse,
    SessionExtendResponse,
)
from app.services.websocket.chat_roulette import WebSocketChatRouletteService
from app.utils.object_storage import ObjectStorageService


class ChatRouletteService:
    """
    Сервис для управления сессиями чат-рулетки.

    Обеспечивает бизнес-логику для поиска партнёров, управления сессиями,
    отправки сообщений, оценки партнёров и обработки жалоб.
    Использует UnitOfWork для работы с базой данных, ObjectStorageService для работы с файлами,
    и WebSocketChatRouletteService для уведомлений в реальном времени.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        oss: ObjectStorageService,
        wcrs: WebSocketChatRouletteService,
    ):
        self.uow = uow
        self.oss = oss
        self.wcrs = wcrs

    async def start_search(
        self, search_request: ChatRouletteSearchRequest, profile_id: UUID
    ) -> ChatRouletteSearchResponse:
        """
        Запускает поиск партнёра для чат-рулетки.

        Проверяет наличие активных поисков или сессий у профиля.
        Если найден подходящий партнёр по интересам, сразу создаёт сессию.
        Если нет - запускает фоновый поиск на 20 секунд.

        Args:
            search_request: Запрос с приоритетными интересами для поиска
            profile_id: Идентификатор профиля, инициирующего поиск

        Returns:
            ChatRouletteSearchResponse: Ответ с информацией о найденной сессии или ошибкой

        Raises:
            ProfileNotFoundError: Если профиль не найден
            AlreadyInSearchError: Если у профиля уже есть активный поиск
            AlreadyInSessionError: Если у профиля уже есть активная сессия
            NoMatchingFoundError: Если не найдено совпадений за отведённое время
        """
        app_logger.info(f"Начало поиска для профиля: {profile_id}")

        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            existing_search = await uow.chat_roulette_search.find_one(
                profile_id=profile_id, is_active=True
            )
            if existing_search:
                raise AlreadyInSearchError()

            existing_session = (
                await uow.chat_roulette_session.find_active_session_by_profile(
                    profile_id
                )
            )
            if existing_session:
                raise AlreadyInSessionError()

            search = await uow.chat_roulette_search.create_or_update_search(
                profile_id=profile_id,
                priority_interest_ids=search_request.priority_interest_ids,
            )

            matched = await self._try_match_profile(
                uow,
                profile_id,
                search_request.priority_interest_ids or [],
            )

            if matched:
                partner_profile_id, matched_interest_id = matched

                await uow.chat_roulette_session.delete_waiting_sessions(
                    partner_profile_id
                )

                waiting_session = (
                    await uow.chat_roulette_session.find_session_by_profile(
                        profile_id, include_completed=False
                    )
                )

                if waiting_session:
                    started_session = await uow.chat_roulette_session.start_session(
                        waiting_session.id, partner_profile_id, matched_interest_id
                    )
                else:
                    session_data = {
                        "profile1_id": profile_id,
                        "profile2_id": partner_profile_id,
                        "matched_interest_id": matched_interest_id,
                        "status": ChatRouletteSessionStatus.ACTIVE,
                        "duration_minutes": 5,
                        "started_at": datetime.now(timezone.utc),
                        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
                    }
                    started_session = await uow.chat_roulette_session.add_one(
                        session_data
                    )

                await uow.chat_roulette_search.deactivate_search(profile_id)
                await uow.chat_roulette_search.deactivate_search(partner_profile_id)

                await uow.commit()

                partner_profile = await uow.profile.get_by_id(partner_profile_id)
                common_interests = await self._get_common_interests(
                    profile_id, partner_profile_id
                )

                app_logger.info(
                    f"Найдено совпадение: {profile_id} с {partner_profile_id}"
                )

                return ChatRouletteSearchResponse(
                    session=ChatRouletteSessionResponse.model_validate(
                        await self._enrich_session_response(
                            started_session,
                            profile_id,
                            partner_profile,
                            common_interests,
                        )
                    ),
                    immediate_match=True,
                    search_id=None,
                )

            session_data = {
                "profile1_id": profile_id,
                "status": ChatRouletteSessionStatus.WAITING,
                "duration_minutes": 5,
            }
            await uow.chat_roulette_session.add_one(session_data)

            await uow.commit()

            try:
                active_session = await asyncio.wait_for(
                    self._background_search_with_timeout(
                        profile_id,
                        search.id,
                        search_request.priority_interest_ids or [],
                    ),
                    timeout=20.0,
                )

                if active_session:
                    return ChatRouletteSearchResponse(
                        session=active_session,
                        immediate_match=True,
                        search_id=None,
                    )
                else:
                    await uow.chat_roulette_session.delete_waiting_sessions(profile_id)
                    await uow.chat_roulette_search.deactivate_search(profile_id)
                    await uow.commit()
                    raise NoMatchingFoundError()

            except asyncio.TimeoutError:
                await uow.chat_roulette_session.delete_waiting_sessions(profile_id)
                await uow.chat_roulette_search.deactivate_search(profile_id)
                await uow.commit()
                raise NoMatchingFoundError()

    async def cancel_search(self, profile_id: UUID) -> bool:
        """
        Отменяет активный поиск партнёра для указанного профиля.

        Args:
            profile_id: Идентификатор профиля, для которого отменяется поиск

        Returns:
            bool: True, если поиск был успешно отменён, False, если активного поиска не было

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        app_logger.info(f"Отмена поиска для профиля: {profile_id}")

        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            deactivated = await uow.chat_roulette_search.deactivate_search(profile_id)

            session = await uow.chat_roulette_session.find_session_by_profile(
                profile_id, include_completed=False
            )

            if session and session.status == ChatRouletteSessionStatus.WAITING:
                await uow.chat_roulette_session.update_session_status(
                    session.id,
                    ChatRouletteSessionStatus.CANCELLED,
                    "Search cancelled by user",
                )

            await uow.commit()

            return deactivated

    async def get_active_session(
        self, profile_id: UUID
    ) -> ChatRouletteSessionResponse | None:
        """
        Возвращает активную сессию чат-рулетки для указанного профиля.

        Args:
            profile_id: Идентификатор профиля, для которого запрашивается активная сессия

        Returns:
            ChatRouletteSessionResponse: Информация об активной сессии с данными о партнёре и общих интересах
            None: Если активной сессии нет

        Raises:
            ProfileNotFoundError: Если профиль не найден
        """
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )

            if not session:
                return None

            partner_profile_id = (
                session.profile2_id
                if session.profile1_id == profile_id
                else session.profile1_id
            )

            if not partner_profile_id:
                return None

            partner_profile = await uow.profile.get_by_id(partner_profile_id)
            common_interests = await self._get_common_interests(
                profile_id, partner_profile_id
            )

            return ChatRouletteSessionResponse.model_validate(
                await self._enrich_session_response(
                    session, profile_id, partner_profile, common_interests
                )
            )

    async def send_message(
        self, profile_id: UUID, content: str
    ) -> ChatRouletteMessageResponse:
        """
        Отправляет сообщение в активной сессии чат-рулетки.

        Проверяет наличие активной сессии, её срок действия и существование партнёра.
        Сохраняет сообщение в базе данных и отправляет уведомление через WebSocket.

        Args:
            profile_id: Идентификатор профиля, отправляющего сообщение
            content: Текст сообщения

        Returns:
            ChatRouletteMessageResponse: Информация об отправленном сообщении

        Raises:
            ProfileNotFoundError: Если профиль не найден
            NoActiveSessionError: Если у профиля нет активной сессии
            SessionExpiredError: Если сессия истекла
            PartnerNotFoundError: Если партнёр не найден в сессии
        """
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )

            if not session:
                raise NoActiveSessionError()

            if session.expires_at and session.expires_at < datetime.now(timezone.utc):
                await uow.chat_roulette_session.update_session_status(
                    session.id, ChatRouletteSessionStatus.COMPLETED, "Session expired"
                )
                await uow.commit()
                raise SessionExpiredError()

            partner_profile_id = (
                session.profile2_id
                if session.profile1_id == profile_id
                else session.profile1_id
            )

            if not partner_profile_id:
                raise PartnerNotFoundError()

            message = await uow.chat_roulette_message.add_one(
                {
                    "session_id": session.id,
                    "sender_profile_id": profile_id,
                    "content": content,
                }
            )

            await uow.commit()

            message_response = ChatRouletteMessageResponse(
                session_id=session.id,
                sender_id=profile_id,
                content=content,
                created_at=message.created_at,
            )

            try:
                await self.wcrs.broadcast_message_sent(
                    session.id, message_response.model_dump(), profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о новом сообщении: {e}"
                )

            return message_response

    async def get_session_messages(
        self, profile_id: UUID, limit: int | None = None, before: datetime | None = None
    ) -> list[ChatRouletteMessageResponse]:
        """
        Возвращает историю сообщений активной сессии текущего профиля.

        Args:
            profile_id: Идентификатор профиля запрашивающего
            limit: Максимальное количество сообщений (None – все)
            before: Дата, до которой брать сообщения (для пагинации)

        Returns:
            Список сообщений в порядке отправки

        Raises:
            NoActiveSessionError: Если у профиля нет активной сессии
        """
        app_logger.info(
            f"Получение истории сообщений активной сессии для профиля: {profile_id}"
        )
        async with self.uow as uow:
            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )
            if not session:
                raise NoActiveSessionError()

            messages = await uow.chat_roulette_message.get_messages_by_session(
                session.id, limit=limit, before=before
            )
            app_logger.info(
                f"Найдено {len(messages)} сообщений для сессии {session.id}"
            )
            return [
                ChatRouletteMessageResponse(
                    session_id=session.id,
                    sender_id=m.sender_profile_id,
                    content=m.content,
                    created_at=m.created_at,
                )
                for m in messages
            ]

    async def extend_session(self, profile_id: UUID) -> SessionExtendResponse:
        """
        Продлевает активную сессию чат-рулетки на фиксированное время.

        Проверяет наличие активной сессии и запрашивает согласие обоих участников.
        Если оба согласны, продлевает сессию на 5 минут и уведомляет через WebSocket.

        Args:
            profile_id: Идентификатор профиля, запрашивающего продление

        Returns:
            SessionExtendResponse: Информация о продлённой сессии

        Raises:
            ProfileNotFoundError: Если профиль не найден
            NoActiveSessionError: Если у профиля нет активной сессии
            ExtensionNotApprovedError: Если партнёр не одобрил продление
            SessionNotFoundError: Если сессия не найдена после продления
        """
        fixed_extension_minutes = 5

        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )

            if not session:
                raise NoActiveSessionError()

            is_profile1 = session.profile1_id == profile_id
            partner_profile_id = (
                session.profile2_id if is_profile1 else session.profile1_id
            )

            if is_profile1:
                session.extension_approved_by_profile1 = True
            else:
                session.extension_approved_by_profile2 = True

            update_data = {
                "extension_approved_by_profile1": session.extension_approved_by_profile1,
                "extension_approved_by_profile2": session.extension_approved_by_profile2,
            }

            await uow.chat_roulette_session.update(session.id, update_data)
            await uow.commit()

            if is_profile1 and not session.extension_approved_by_profile2:
                try:
                    await self.wcrs.broadcast_extension_request(
                        session.id, profile_id, partner_profile_id
                    )
                except Exception as e:
                    app_logger.error(
                        f"Ошибка при отправке WebSocket уведомления о запросе продления: {e}"
                    )
                raise ExtensionNotApprovedError()
            elif not is_profile1 and not session.extension_approved_by_profile1:
                try:
                    await self.wcrs.broadcast_extension_request(
                        session.id, profile_id, partner_profile_id
                    )
                except Exception as e:
                    app_logger.error(
                        f"Ошибка при отправке WebSocket уведомления о запросе продления: {e}"
                    )
                raise ExtensionNotApprovedError()

            try:
                await self.wcrs.broadcast_extension_approved(
                    session.id, profile_id, partner_profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления об утверждении продления: {e}"
                )

            extended_session = await uow.chat_roulette_session.extend_session(
                session.id, fixed_extension_minutes
            )

            if not extended_session:
                raise SessionNotFoundError()

            reset_data = {
                "extension_approved_by_profile1": False,
                "extension_approved_by_profile2": False,
            }
            await uow.chat_roulette_session.update(session.id, reset_data)
            await uow.commit()

            response = SessionExtendResponse(
                session_id=session.id,
                extended_minutes=fixed_extension_minutes,
                new_expires_at=extended_session.expires_at.isoformat(),
            )

            try:
                await self.wcrs.broadcast_session_extended(
                    session.id,
                    profile_id,
                    fixed_extension_minutes,
                    extended_session.expires_at,
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о продлении сессии: {e}"
                )

            return response

    async def reject_extension(self, profile_id: UUID) -> None:
        """
        Отказывает в продлении сессии чат-рулетки (вызывается партнёром).

        Сбрасывает флаги одобрения продления у обоих участников,
        чтобы при необходимости можно было повторить запрос.
        Отправляет уведомление EXTENSION_REJECTED обоим участникам.

        Args:
            profile_id: Идентификатор профиля, отказывающегося от продления

        Raises:
            NoActiveSessionError: Если у профиля нет активной сессии
        """
        app_logger.info(f"Отказ в продлении сессии от профиля {profile_id}")
        async with self.uow as uow:
            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )
            if not session:
                raise NoActiveSessionError()

            partner_id = (
                session.profile2_id
                if session.profile1_id == profile_id
                else session.profile1_id
            )

            await uow.chat_roulette_session.update(
                session.id,
                {
                    "extension_approved_by_profile1": False,
                    "extension_approved_by_profile2": False,
                },
            )
            await uow.commit()

        await self.wcrs.broadcast_extension_rejected(session.id, profile_id, partner_id)

    async def cancel_extension_request(self, profile_id: UUID) -> None:
        """
        Отменяет собственный запрос на продление сессии (вызывается инициатором)
        до того, как партнёр ответил на запрос.

        Сбрасывает флаг одобрения только инициатора.
        Отправляет уведомление EXTENSION_CANCELLED обоим участникам.

        Args:
            profile_id: Идентификатор профиля, отменяющего запрос

        Raises:
            NoActiveSessionError: Если у профиля нет активной сессии
        """
        app_logger.info(f"Отмена запроса на продление от профиля {profile_id}")
        async with self.uow as uow:
            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )
            if not session:
                raise NoActiveSessionError()

            is_profile1 = session.profile1_id == profile_id
            partner_id = session.profile2_id if is_profile1 else session.profile1_id

            update_data = {
                "extension_approved_by_profile1": (
                    False if is_profile1 else session.extension_approved_by_profile1
                ),
                "extension_approved_by_profile2": (
                    False if not is_profile1 else session.extension_approved_by_profile2
                ),
            }
            await uow.chat_roulette_session.update(session.id, update_data)
            await uow.commit()

        await self.wcrs.broadcast_extension_cancelled(
            session.id, profile_id, partner_id
        )

    async def end_session(self, profile_id: UUID, reason: str) -> bool:
        """
        Завершает активную сессию чат-рулетки с указанием причины.

        Обновляет статус сессии на LEFT и уведомляет партнёра через WebSocket.

        Args:
            profile_id: Идентификатор профиля, завершающего сессию
            reason: Причина завершения сессии

        Returns:
            bool: True, если сессия успешно завершена

        Raises:
            ProfileNotFoundError: Если профиль не найден
            NoActiveSessionError: Если у профиля нет активной сессии
            SessionAlreadyEndedError: Если сессия уже завершена
        """
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )

            if not session:
                raise NoActiveSessionError()

            if session.status != ChatRouletteSessionStatus.ACTIVE:
                raise SessionAlreadyEndedError()

            full_reason = f"Left by user: {reason}"
            await uow.chat_roulette_session.update_session_status(
                session.id, ChatRouletteSessionStatus.LEFT, full_reason
            )

            await uow.commit()

            try:
                await self.wcrs.broadcast_session_ended(
                    session.id, profile_id, full_reason
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о завершении сессии: {e}"
                )

            return True

    async def rate_partner(
        self, profile_id: UUID, rating_request: ChatRouletteRatingRequest
    ) -> bool:
        """
        Ставит оценку партнёру по завершённой сессии чат-рулетки.

        Обновляет рейтинг партнёра и корректирует его репутацию.
        Рейтинг от 1 до 5, где 3 - нейтральная оценка.
        Репутация изменяется на (rating - 3) * 0.1 и ограничена диапазоном [0.0, 5.0].

        Args:
            profile_id: Идентификатор профиля, оставляющего оценку
            rating_request: Запрос с оценкой (1-5) и опциональным отзывом

        Returns:
            bool: True, если оценка успешно сохранена

        Raises:
            ProfileNotFoundError: Если профиль не найден
            NoActiveSessionError: Если у профиля нет завершённой сессии
            CannotRateNonCompletedSessionError: Если сессия не завершена
            PartnerNotFoundError: Если партнёр не найден в сессии
            CannotRateYourselfError: Если профиль пытается оценить сам себя
            AlreadyRatedError: Если профиль уже ставил оценку в этой сессии
        """
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            session = await uow.chat_roulette_session.find_session_by_profile(
                profile_id, include_completed=True
            )

            if not session:
                raise NoActiveSessionError()

            if session.status != ChatRouletteSessionStatus.COMPLETED:
                raise CannotRateNonCompletedSessionError(session.status)

            partner_profile_id = (
                session.profile2_id
                if session.profile1_id == profile_id
                else session.profile1_id
            )

            if not partner_profile_id:
                raise PartnerNotFoundError()

            if profile_id == partner_profile_id:
                raise CannotRateYourselfError()

            if (session.profile1_id == profile_id and session.rating_from_1_to_2) or (
                session.profile2_id == profile_id and session.rating_from_2_to_1
            ):
                raise AlreadyRatedError()

            await uow.chat_roulette_session.add_rating(
                session.id, profile_id, partner_profile_id, rating_request.rating
            )

            new_reputation = await uow.chat_roulette_session.calculate_reputation(
                partner_profile_id
            )
            await uow.profile.update(
                partner_profile_id, {"reputation_score": new_reputation}
            )
            await uow.commit()

            return True

    async def report_partner(
        self,
        profile_id: UUID,
        report_request: ChatRouletteReportRequest,
    ) -> bool:
        """
        Сообщает о нарушении правил партнёром в активной сессии чат-рулетки.

        Завершает сессию со статусом REPORTED, сохраняет информацию о жалобе
        и уведомляет через WebSocket.

        Args:
            profile_id: Идентификатор профиля, подающего жалобу
            report_request: Запрос с причиной жалобы и деталями инцидента

        Returns:
            bool: True, если жалоба успешно обработана

        Raises:
            ProfileNotFoundError: Если профиль не найден
            NoActiveSessionError: Если у профиля нет активной сессии
            PartnerNotFoundError: Если партнёр не найден в сессии
        """
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            session = await uow.chat_roulette_session.find_active_session_by_profile(
                profile_id
            )

            if not session:
                raise NoActiveSessionError()

            partner_profile_id = (
                session.profile2_id
                if session.profile1_id == profile_id
                else session.profile1_id
            )

            if not partner_profile_id:
                raise PartnerNotFoundError()

            full_reason = f"Reported: {report_request.reason}"
            await uow.chat_roulette_session.update_session_status(
                session.id,
                ChatRouletteSessionStatus.REPORTED,
                full_reason,
            )

            await uow.chat_roulette_report.add_one(
                {
                    "session_id": session.id,
                    "reporter_profile_id": profile_id,
                    "reported_profile_id": partner_profile_id,
                    "reason": report_request.reason,
                    "details": report_request.details,
                }
            )

            await uow.commit()

            app_logger.warning(
                f"Профиль {profile_id} пожаловался на {partner_profile_id}: {report_request.reason} - {report_request.details}"
            )

            try:
                await self.wcrs.broadcast_session_ended(
                    session.id, profile_id, full_reason
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о репорте сессии: {e}"
                )

            return True

    async def _try_match_profile(
        self, uow, profile_id: UUID, priority_interest_ids: list[UUID]
    ) -> tuple[UUID, UUID | None] | None:
        """
        Пытается найти подходящего партнёра для указанного профиля.

        Правила совместимости:
        - Если у текущего профиля есть интересы, он может соединиться только с теми,
        у кого тоже есть интересы и имеется хотя бы один общий интерес.
        - Если у текущего профиля нет интересов, он может соединиться только с такими же
        профилями без интересов (матч без темы).
        - Репутация не влияет на подбор.

        Приоритетные интересы (если указаны) дают бонус к score (×2 за каждое совпадение),
        но не могут создать матч при отсутствии общих интересов.

        Возвращает:
            - Идентификатор найденного профиля и идентификатор общего интереса
            (приоритетного, если есть, иначе первого общего).
            - None, если подходящий партнёр не найден.
        """
        current_profile_interests = await uow.profile.get_profile_interests(profile_id)
        current_interest_ids = {interest.id for interest in current_profile_interests}
        current_has_interests = len(current_interest_ids) > 0

        waiting_sessions = await uow.chat_roulette_session.find_matching_sessions(
            profile_id
        )

        best_match = None
        best_score = -1
        best_common_interest = None

        for session, partner_priority_ids in waiting_sessions:
            partner_profile_id = session.profile1_id
            partner_profile_interests = await uow.profile.get_profile_interests(
                partner_profile_id
            )
            partner_interest_ids = {
                interest.id for interest in partner_profile_interests
            }
            partner_has_interests = len(partner_interest_ids) > 0

            if current_has_interests:
                if not partner_has_interests:
                    continue
                common_interests = current_interest_ids.intersection(
                    partner_interest_ids
                )
                if not common_interests:
                    continue
            else:
                if partner_has_interests:
                    continue
                common_interests = set()

            score = len(common_interests)
            if priority_interest_ids:
                priority_matches = len(
                    set(priority_interest_ids).intersection(partner_interest_ids)
                )
                score += priority_matches * 2

            if not current_has_interests:
                score = 1

            if score > best_score:
                best_score = score

                if common_interests:
                    mutual_priority = set(priority_interest_ids).intersection(
                        partner_priority_ids or []
                    )
                    mutual_priority_common = mutual_priority.intersection(
                        common_interests
                    )
                    if mutual_priority_common:
                        best_common_interest = next(iter(mutual_priority_common))
                    else:
                        priority_common = set(priority_interest_ids).intersection(
                            common_interests
                        )
                        if priority_common:
                            best_common_interest = next(iter(priority_common))
                        else:
                            best_common_interest = next(iter(common_interests))
                else:
                    best_common_interest = None

                best_match = (partner_profile_id, best_common_interest)

        return best_match

    async def _background_search_with_timeout(
        self, profile_id: UUID, search_id: UUID, priority_interest_ids: list[UUID]
    ) -> ChatRouletteSessionResponse | None:
        """
        Выполняет фоновый поиск партнёра для чат-рулетки с таймаутом.

        Проверяет наличие активной сессии или подходящего партнёра в течение 10 попыток.
        Если сессия или партнёр найдены, возвращает информацию о сессии.
        Если поиск не удался или отменён, возвращает None.

        Args:
            profile_id: Идентификатор профиля, для которого выполняется поиск
            search_id: Идентификатор активного поиска
            priority_interest_ids: Список приоритетных интересов для поиска

        Returns:
            ChatRouletteSessionResponse | None:
                - Информация о найденной сессии, если поиск успешен
                - None, если поиск не удался или был отменён
        """
        async with UnitOfWork() as uow:
            for attempt in range(10):
                active_session = (
                    await uow.chat_roulette_session.find_active_session_by_profile(
                        profile_id
                    )
                )

                if active_session:
                    partner_profile_id = (
                        active_session.profile2_id
                        if active_session.profile1_id == profile_id
                        else active_session.profile1_id
                    )

                    if partner_profile_id:
                        partner_profile = await uow.profile.get_by_id(
                            partner_profile_id
                        )
                        common_interests = await self._get_common_interests(
                            profile_id, partner_profile_id
                        )

                        app_logger.info(
                            f"Фоновый поиск: найдена активная сессия для профиля {profile_id}"
                        )
                        return ChatRouletteSessionResponse.model_validate(
                            await self._enrich_session_response(
                                active_session,
                                profile_id,
                                partner_profile,
                                common_interests,
                            )
                        )

                search = await uow.chat_roulette_search.get_by_id(search_id)

                if search:
                    await uow.session.refresh(search)

                if not search or not search.is_active:
                    return None

                matched = await self._try_match_profile(
                    uow, profile_id, priority_interest_ids
                )

                if matched:
                    partner_profile_id, matched_interest_id = matched

                    await uow.chat_roulette_session.delete_waiting_sessions(
                        partner_profile_id
                    )

                    waiting_session = (
                        await uow.chat_roulette_session.find_session_by_profile(
                            profile_id, include_completed=False
                        )
                    )

                    started_session = await uow.chat_roulette_session.start_session(
                        waiting_session.id, partner_profile_id, matched_interest_id
                    )

                    await uow.chat_roulette_search.deactivate_search(profile_id)
                    await uow.chat_roulette_search.deactivate_search(partner_profile_id)

                    await uow.commit()

                    partner_profile = await uow.profile.get_by_id(partner_profile_id)
                    common_interests = await self._get_common_interests(
                        profile_id, partner_profile_id
                    )

                    return ChatRouletteSessionResponse.model_validate(
                        await self._enrich_session_response(
                            started_session,
                            profile_id,
                            partner_profile,
                            common_interests,
                        )
                    )

                if attempt < 9:
                    await asyncio.sleep(2)

        return None

    async def _get_common_interests(
        self, profile1_id: UUID, profile2_id: UUID
    ) -> list[UUID]:
        """
        Возвращает список общих интересов для двух профилей.

        Args:
            profile1_id: Идентификатор первого профиля
            profile2_id: Идентификатор второго профиля

        Returns:
            list[UUID]: Список идентификаторов общих интересов
        """
        async with UnitOfWork() as uow:
            profile1_interests = await uow.profile.get_profile_interests(profile1_id)
            profile1_interest_ids = {interest.id for interest in profile1_interests}

            profile2_interests = await uow.profile.get_profile_interests(profile2_id)
            profile2_interest_ids = {interest.id for interest in profile2_interests}

            return list(profile1_interest_ids.intersection(profile2_interest_ids))

    async def _enrich_session_response(
        self, session, profile_id: UUID, partner_profile=None, common_interests=None
    ) -> dict:
        response = {
            "id": session.id,
            "profile1_id": session.profile1_id,
            "profile2_id": session.profile2_id,
            "matched_interest_id": session.matched_interest_id,
            "status": session.status,
            "duration_minutes": session.duration_minutes,
            "extension_minutes": session.extension_minutes,
            "started_at": (
                session.started_at.isoformat() if session.started_at else None
            ),
            "expires_at": (
                session.expires_at.isoformat() if session.expires_at else None
            ),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "created_at": session.created_at.isoformat(),
            "extension_approved_by_profile1": session.extension_approved_by_profile1,
            "extension_approved_by_profile2": session.extension_approved_by_profile2,
        }

        partner_id = None
        if session.profile1_id == profile_id:
            partner_id = session.profile2_id
        elif session.profile2_id == profile_id:
            partner_id = session.profile1_id

        partner_online = False
        if partner_id:
            partner_online = self.wcrs.is_profile_connected(session.id, partner_id)
        response["partner_online"] = partner_online

        if partner_profile:
            avatar_url = await self.oss.get_avatar_url(partner_profile.id)
            response["matched_profile"] = {
                "id": partner_profile.id,
                "username": partner_profile.username,
                "bio": partner_profile.bio,
                "reputation_score": partner_profile.reputation_score,
                "avatar_url": avatar_url,
            }

        if common_interests:
            response["common_interests"] = common_interests

        if session.expires_at and session.status == ChatRouletteSessionStatus.ACTIVE:
            remaining = (
                session.expires_at - datetime.now(timezone.utc)
            ).total_seconds()
            response["time_remaining"] = max(0, int(remaining))

        return response
