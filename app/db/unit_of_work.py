from abc import ABC, abstractmethod

from app.db.database import async_session_maker
from app.repositories import (
    InterestRepository,
    ProfileInterestRepository,
    ProfileRepository,
    RoomMessageRepository,
    RoomParticipantRepository,
    RoomRepository,
    UserRepository,
)


class IUnitOfWork(ABC):
    """
    Интерфейс для реализации паттерна Unit of Work
    Определяет базовые методы для управления транзакциями в базе данных
    """

    user: UserRepository
    profile: ProfileRepository
    interest: InterestRepository
    profile_interest: ProfileInterestRepository
    room: RoomRepository
    room_participant: RoomParticipantRepository
    room_message: RoomMessageRepository

    @abstractmethod
    async def __aenter__(self):
        """Контекстный менеджер для входа в транзакцию"""

        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args):
        """Контекстный менеджер для выхода из транзакции"""

        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        """Подтверждение транзакции"""

        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        """Откат транзакции"""

        raise NotImplementedError


class UnitOfWork(IUnitOfWork):
    """
    Реализация паттерна Unit of Work
    Управляет сессиями базы данных и транзакциями
    """

    def __init__(self):
        self.session_maker = async_session_maker
        self.session = None

    async def __aenter__(self):
        try:
            self.session = self.session_maker()

            self.user = UserRepository(self.session)
            self.profile = ProfileRepository(self.session)
            self.interest = InterestRepository(self.session)
            self.profile_interest = ProfileInterestRepository(self.session)
            self.room = RoomRepository(self.session)
            self.room_participant = RoomParticipantRepository(self.session)
            self.room_message = RoomMessageRepository(self.session)

            return self

        except Exception as e:
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.rollback()
        finally:
            if self.session is not None:
                await self.session.close()

            self.session = None

    async def commit(self):
        if self.session is None:
            raise RuntimeError("Cannot commit: session is None")

        await self.session.commit()

    async def rollback(self):
        if self.session is None:
            return

        await self.session.rollback()
