from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

class IRepository(ABC):
    """
    Интерфейс для репозитория
    Определяет базовые методы для работы с моделями данных
    """

    @abstractmethod
    async def add_one(self, data: dict) -> Any:
        """Добавление одной записи"""

        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[Any]:
        """Получение записи по ID"""

        raise NotImplementedError

    @abstractmethod
    async def find_all(self, **filters) -> List[Any]:
        """Поиск всех записей с фильтрацией"""

        raise NotImplementedError

    @abstractmethod
    async def find_one(self, **filters) -> Optional[Any]:
        """Поиск одной записи с фильтрацией"""

        raise NotImplementedError

    @abstractmethod
    async def update(self, id: UUID, data: dict) -> Optional[Any]:
        """Обновление записи"""

        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Удаление записи"""

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

    async def get_by_id(self, id: UUID) -> Optional[Any]:
        return await self.session.get(self.model, id)

    async def find_all(self, **filters) -> List[Any]:
        stmt = select(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_one(self, **filters) -> Optional[Any]:
        stmt = select(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: UUID, data: dict) -> Optional[Any]:
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