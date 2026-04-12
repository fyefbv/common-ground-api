from typing import AsyncGenerator

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_async_session
from app.main import app

load_dotenv(".test.env", override=True)

from app.core.config import settings

engine = create_async_engine(settings.ASYNC_DATABASE_URL)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_async_session():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_s3(mocker):
    mock = mocker.patch("app.utils.object_storage.ObjectStorageService")
    mock.return_value.upload_avatar = mocker.AsyncMock(
        return_value="http://fake.url/avatar.jpg"
    )
    mock.return_value.get_avatar_url = mocker.AsyncMock(
        return_value="http://fake.url/avatar.jpg"
    )
    mock.return_value.delete_avatar = mocker.AsyncMock()
    return mock
