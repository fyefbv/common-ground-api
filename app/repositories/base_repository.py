from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class IRepository(ABC):
    """
    Интерфейс для репозитория
    Определяет базовые методы для работы с моделями данных
    """

    @abstractmethod
    async def add_one(self, data: dict) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def find_all(self, **filters) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    async def find_one(self, **filters) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, id: UUID, data: dict) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        raise NotImplementedError

class Repository(IRepository):
    """
    Реализация репозитория
    Обеспечивает доступ к данным через ORM
    """

    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict) -> Any:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID) -> Any | None:
        return await self.session.get(self.model, id)

    async def find_all(self, **filters) -> list[Any]:
        stmt = select(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_one(self, **filters) -> Any | None:
        stmt = select(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: UUID, data: dict) -> Any | None:
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True