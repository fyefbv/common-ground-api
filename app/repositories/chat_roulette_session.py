from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, desc, func, join, or_, select, update

from app.db.models.chat_roulette_search import ChatRouletteSearch
from app.db.models.chat_roulette_session import (
    ChatRouletteSession,
    ChatRouletteSessionStatus,
)
from app.repositories.base import Repository


class ChatRouletteSessionRepository(Repository):
    model = ChatRouletteSession

    async def find_waiting_sessions(
        self, exclude_profile_id: UUID | None = None, limit: int = 10
    ) -> list[ChatRouletteSession]:
        stmt = select(self.model).where(
            self.model.status == ChatRouletteSessionStatus.WAITING,
            self.model.profile2_id.is_(None),
        )

        if exclude_profile_id:
            stmt = stmt.where(self.model.profile1_id != exclude_profile_id)

        stmt = stmt.order_by(self.model.created_at).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_active_session_by_profile(
        self, profile_id: UUID
    ) -> ChatRouletteSession | None:
        stmt = select(self.model).where(
            or_(
                self.model.profile1_id == profile_id,
                self.model.profile2_id == profile_id,
            ),
            self.model.status == ChatRouletteSessionStatus.ACTIVE,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_session_by_profile(
        self, profile_id: UUID, include_completed: bool = False
    ) -> ChatRouletteSession | None:
        status_filter = [
            ChatRouletteSessionStatus.ACTIVE,
            ChatRouletteSessionStatus.WAITING,
        ]
        if include_completed:
            status_filter.extend(
                [
                    ChatRouletteSessionStatus.COMPLETED,
                    ChatRouletteSessionStatus.LEFT,
                    ChatRouletteSessionStatus.REPORTED,
                ]
            )

        stmt = (
            select(self.model)
            .where(
                or_(
                    self.model.profile1_id == profile_id,
                    self.model.profile2_id == profile_id,
                ),
                self.model.status.in_(status_filter),
            )
            .order_by(desc(self.model.created_at))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_matching_sessions(
        self, profile_id: UUID
    ) -> list[ChatRouletteSession]:
        stmt = (
            select(self.model, ChatRouletteSearch.priority_interest_ids)
            .where(
                self.model.status == ChatRouletteSessionStatus.WAITING,
                self.model.profile2_id.is_(None),
                self.model.profile1_id != profile_id,
            )
            .join(
                ChatRouletteSearch,
                ChatRouletteSearch.profile_id == self.model.profile1_id,
            )
            .where(ChatRouletteSearch.is_active == True)
        )

        stmt = stmt.order_by(self.model.created_at)

        result = await self.session.execute(stmt)
        return result.all()

    async def start_session(
        self,
        session_id: UUID,
        profile2_id: UUID,
        matched_interest_id: UUID | None = None,
    ) -> ChatRouletteSession | None:
        stmt = (
            update(self.model)
            .where(
                self.model.id == session_id,
                self.model.status == ChatRouletteSessionStatus.WAITING,
            )
            .values(
                profile2_id=profile2_id,
                matched_interest_id=matched_interest_id,
                status=ChatRouletteSessionStatus.ACTIVE,
                started_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            )
            .returning(self.model)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        if result:
            return await self.get_by_id(session_id)
        return None

    async def update_session_status(
        self,
        session_id: UUID,
        status: ChatRouletteSessionStatus,
        end_reason: str | None = None,
    ) -> None:
        update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}

        if status in [
            ChatRouletteSessionStatus.COMPLETED,
            ChatRouletteSessionStatus.LEFT,
            ChatRouletteSessionStatus.REPORTED,
            ChatRouletteSessionStatus.CANCELLED,
        ]:
            update_data["ended_at"] = datetime.now(timezone.utc)
            if end_reason:
                update_data["end_reason"] = end_reason

        stmt = (
            update(self.model).where(self.model.id == session_id).values(**update_data)
        )

        await self.session.execute(stmt)

    async def extend_session(
        self, session_id: UUID, minutes: int = 5
    ) -> ChatRouletteSession | None:
        session = await self.get_by_id(session_id)
        if not session or session.expires_at is None:
            return None

        new_expires_at = session.expires_at + timedelta(minutes=minutes)

        extension_minutes = (session.extension_minutes or 0) + minutes

        stmt = (
            update(self.model)
            .where(
                self.model.id == session_id,
                self.model.status == ChatRouletteSessionStatus.ACTIVE,
            )
            .values(
                expires_at=new_expires_at,
                extension_minutes=extension_minutes,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(self.model)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return await self.get_by_id(session_id)

    async def add_rating(
        self, session_id: UUID, from_profile_id: UUID, to_profile_id: UUID, rating: int
    ) -> None:
        session = await self.get_by_id(session_id)
        if not session:
            return

        update_data = {}
        if (
            session.profile1_id == from_profile_id
            and session.profile2_id == to_profile_id
        ):
            update_data["rating_from_1_to_2"] = rating
        elif (
            session.profile2_id == from_profile_id
            and session.profile1_id == to_profile_id
        ):
            update_data["rating_from_2_to_1"] = rating

        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            stmt = (
                update(self.model)
                .where(self.model.id == session_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)

    async def get_expiring_sessions(
        self, minutes_before: int = 1
    ) -> list[ChatRouletteSession]:
        cutoff = datetime.now(timezone.utc) + timedelta(minutes=minutes_before)

        stmt = select(self.model).where(
            self.model.status == ChatRouletteSessionStatus.ACTIVE,
            self.model.expires_at <= cutoff,
            self.model.expires_at > datetime.now(timezone.utc),
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_expired_sessions(self) -> list[ChatRouletteSession]:
        stmt = select(self.model).where(
            self.model.status == ChatRouletteSessionStatus.ACTIVE,
            self.model.expires_at <= datetime.now(timezone.utc),
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_profile_statistics(self, profile_id: UUID) -> tuple[int, int, float]:
        total_sessions_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(
                or_(
                    self.model.profile1_id == profile_id,
                    self.model.profile2_id == profile_id,
                ),
                self.model.status.in_(
                    [
                        ChatRouletteSessionStatus.COMPLETED,
                        ChatRouletteSessionStatus.LEFT,
                    ]
                ),
            )
        )
        total_result = await self.session.execute(total_sessions_stmt)
        total_sessions = total_result.scalar() or 0

        completed_sessions_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(
                or_(
                    self.model.profile1_id == profile_id,
                    self.model.profile2_id == profile_id,
                ),
                self.model.status == ChatRouletteSessionStatus.COMPLETED,
            )
        )
        completed_result = await self.session.execute(completed_sessions_stmt)
        completed_sessions = completed_result.scalar() or 0

        rating_stmt = select(func.avg(self.model.rating_from_2_to_1)).where(
            self.model.profile1_id == profile_id,
            self.model.rating_from_2_to_1.is_not(None),
        )
        rating_result = await self.session.execute(rating_stmt)
        avg_rating = rating_result.scalar() or 0.0

        rating2_stmt = select(func.avg(self.model.rating_from_1_to_2)).where(
            self.model.profile2_id == profile_id,
            self.model.rating_from_1_to_2.is_not(None),
        )
        rating2_result = await self.session.execute(rating2_stmt)
        avg_rating2 = rating2_result.scalar() or 0.0

        total_avg = (
            (avg_rating + avg_rating2) / 2
            if avg_rating > 0 and avg_rating2 > 0
            else max(avg_rating, avg_rating2)
        )

        return total_sessions, completed_sessions, total_avg

    async def delete_waiting_sessions(self, profile_id: UUID) -> None:
        from sqlalchemy import delete, or_

        stmt = delete(self.model).where(
            or_(
                self.model.profile1_id == profile_id,
                self.model.profile2_id == profile_id,
            ),
            self.model.status == ChatRouletteSessionStatus.WAITING,
        )
        await self.session.execute(stmt)
