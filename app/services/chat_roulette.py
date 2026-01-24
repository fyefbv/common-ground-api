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
    ChatRouletteStatisticsResponse,
    SessionExtendResponse,
)
from app.utils.object_storage import ObjectStorageService


class ChatRouletteService:
    def __init__(self, uow: UnitOfWork, object_storage_service: ObjectStorageService):
        self.uow = uow
        self.object_storage_service = object_storage_service

    async def start_search(
        self, search_request: ChatRouletteSearchRequest, profile_id: UUID
    ) -> ChatRouletteSearchResponse:
        app_logger.info(f"Начало поиска для профиля: {profile_id}")

        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            existing_search = await uow.chat_roulette_search.find_active_search(
                profile_id
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
                max_wait_time_minutes=search_request.max_wait_time_minutes,
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
                            started_session, partner_profile, common_interests
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
            session = await uow.chat_roulette_session.add_one(session_data)

            await uow.commit()

            asyncio.create_task(
                self._background_search(
                    profile_id,
                    search.id,
                    search_request.priority_interest_ids or [],
                )
            )

            if not hasattr(self, "_cleanup_task") or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(
                    self._background_session_cleanup()
                )
                app_logger.info("Запущена задача очистки сессий в фоне")

            return ChatRouletteSearchResponse(
                session=ChatRouletteSessionResponse.model_validate(
                    await self._enrich_session_response(session)
                ),
                immediate_match=False,
                search_id=search.id,
            )

    async def cancel_search(self, profile_id: UUID) -> bool:
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
                    session, partner_profile, common_interests
                )
            )

    async def send_message(
        self, profile_id: UUID, content: str
    ) -> ChatRouletteMessageResponse:
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

            return ChatRouletteMessageResponse(
                session_id=session.id,
                sender_id=profile_id,
                content=content,
                created_at=message.created_at,
            )

    async def extend_session(self, profile_id: UUID) -> SessionExtendResponse:
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
                raise ExtensionNotApprovedError()
            elif not is_profile1 and not session.extension_approved_by_profile1:
                raise ExtensionNotApprovedError()

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

            return SessionExtendResponse(
                session_id=session.id,
                extended_minutes=fixed_extension_minutes,
                new_expires_at=extended_session.expires_at.isoformat(),
            )

    async def end_session(self, profile_id: UUID, reason: str) -> bool:
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

            await uow.chat_roulette_session.update_session_status(
                session.id, ChatRouletteSessionStatus.LEFT, f"Left by user: {reason}"
            )

            await uow.commit()

            return True

    async def rate_partner(
        self, profile_id: UUID, rating_request: ChatRouletteRatingRequest
    ) -> bool:
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

            partner_profile = await uow.profile.get_by_id(partner_profile_id)
            if partner_profile:
                new_reputation = (
                    partner_profile.reputation_score + (rating_request.rating - 3) * 0.1
                )
                new_reputation = max(0.0, min(5.0, new_reputation))

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

            await uow.chat_roulette_session.update_session_status(
                session.id,
                ChatRouletteSessionStatus.REPORTED,
                f"Reported: {report_request.reason}",
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

            return True

    async def get_statistics(self, profile_id: UUID) -> ChatRouletteStatisticsResponse:
        async with self.uow as uow:
            profile = await uow.profile.get_by_id(profile_id)
            if not profile:
                raise ProfileNotFoundError(profile_id)

            total, completed, avg_rating = (
                await uow.chat_roulette_session.get_profile_statistics(profile_id)
            )

            return ChatRouletteStatisticsResponse(
                total_sessions=total,
                completed_sessions=completed,
                average_rating=round(avg_rating, 2),
                completion_rate=round(completed / total * 100, 2) if total > 0 else 0,
            )

    async def _try_match_profile(
        self, uow, profile_id: UUID, priority_interest_ids: list[UUID]
    ) -> tuple[UUID, UUID | None] | None:
        MIN_MATCH_SCORE = 1

        current_profile_interests = await uow.profile.get_profile_interests(profile_id)
        current_interest_ids = {interest.id for interest in current_profile_interests}

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

            common_interests = current_interest_ids.intersection(partner_interest_ids)

            score = len(common_interests)

            if priority_interest_ids:
                priority_matches = len(
                    set(priority_interest_ids).intersection(partner_interest_ids)
                )
                score += priority_matches * 2

            partner_profile = await uow.profile.get_by_id(partner_profile_id)
            if partner_profile:
                score += int(partner_profile.reputation_score)

            if score > best_score and score >= MIN_MATCH_SCORE:
                best_score = score

                priority_common_interests = set(priority_interest_ids).intersection(
                    common_interests
                )

                mutual_priority_interests = set(priority_interest_ids).intersection(
                    partner_priority_ids or []
                )
                mutual_priority_common = mutual_priority_interests.intersection(
                    common_interests
                )

                if mutual_priority_common:
                    best_common_interest = next(iter(mutual_priority_common))
                elif priority_common_interests:
                    best_common_interest = next(iter(priority_common_interests))
                else:
                    best_common_interest = (
                        next(iter(common_interests), None) if common_interests else None
                    )

                best_match = (partner_profile_id, best_common_interest)

        return best_match

    async def _background_search(
        self, profile_id: UUID, search_id: UUID, priority_interest_ids: list[UUID]
    ):
        try:
            await asyncio.sleep(2)

            async with UnitOfWork() as uow:
                search = await uow.chat_roulette_search.get_by_id(search_id)
                if not search or not search.is_active:
                    return

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

                    app_logger.info(
                        f"Найдено совпадение в фоне: {profile_id} с {partner_profile_id}"
                    )
                else:
                    await uow.chat_roulette_search.increase_search_score(search_id, 1)
                    await uow.commit()

                    asyncio.create_task(
                        self._background_search(
                            profile_id, search_id, priority_interest_ids
                        )
                    )

        except Exception as e:
            app_logger.error(f"Ошибка фонового поиска: {e}")

    async def _background_session_cleanup(self):
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

                        expiring_soon_sessions = (
                            await uow.chat_roulette_session.get_expiring_sessions(
                                minutes_before=2
                            )
                        )

                        if expiring_soon_sessions:
                            next_expiry = min(
                                session.expires_at for session in expiring_soon_sessions
                            )
                            time_until_next = (
                                next_expiry - datetime.now(timezone.utc)
                            ).total_seconds()
                            await asyncio.sleep(max(0, min(time_until_next, 120)))
                        else:
                            await asyncio.sleep(60)

                except Exception as e:
                    app_logger.error(f"Ошибка очистки сессий в фоне: {e}")
                    await asyncio.sleep(60)

        except asyncio.CancelledError:
            app_logger.info("Задача очистки сессий в фоне отменена")
            raise

    async def _get_common_interests(
        self, profile1_id: UUID, profile2_id: UUID
    ) -> list[UUID]:
        async with UnitOfWork() as uow:
            profile1_interests = await uow.profile.get_profile_interests(profile1_id)
            profile1_interest_ids = {interest.id for interest in profile1_interests}

            profile2_interests = await uow.profile.get_profile_interests(profile2_id)
            profile2_interest_ids = {interest.id for interest in profile2_interests}

            return list(profile1_interest_ids.intersection(profile2_interest_ids))

    async def _enrich_session_response(
        self, session, partner_profile=None, common_interests=None
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

        if partner_profile:
            avatar_url = await self.object_storage_service.get_avatar_url(
                partner_profile.id
            )
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
