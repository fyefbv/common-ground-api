from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(url=settings.ASYNC_DATABASE_URL)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session():
    async with async_session_maker() as session:
        yield session


class Base(AsyncAttrs, DeclarativeBase):
    pass
