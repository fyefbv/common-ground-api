from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, desc, func, or_, select, update

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

    async def get_total_completed_sessions(self, profile_id: UUID) -> int:
        stmt = (
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
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete_waiting_sessions(self, profile_id: UUID) -> None:
        stmt = delete(self.model).where(
            or_(
                self.model.profile1_id == profile_id,
                self.model.profile2_id == profile_id,
            ),
            self.model.status == ChatRouletteSessionStatus.WAITING,
        )
        await self.session.execute(stmt)

    async def calculate_reputation(self, profile_id: UUID) -> float:
        stmt1 = select(self.model.rating_from_2_to_1).where(
            self.model.profile1_id == profile_id,
            self.model.rating_from_2_to_1.is_not(None),
        )
        stmt2 = select(self.model.rating_from_1_to_2).where(
            self.model.profile2_id == profile_id,
            self.model.rating_from_1_to_2.is_not(None),
        )

        ratings = []
        result1 = await self.session.execute(stmt1)
        ratings.extend([row[0] for row in result1.all() if row[0] is not None])
        result2 = await self.session.execute(stmt2)
        ratings.extend([row[0] for row in result2.all() if row[0] is not None])

        if not ratings:
            return 0.0
        return round(sum(ratings) / len(ratings), 2)
