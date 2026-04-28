from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.user import UserCreate
from app.services.user import UserService


@pytest.mark.asyncio
async def test_create_user_already_exists():
    mock_uow = AsyncMock()
    mock_uow.user.find_one = AsyncMock(return_value=MagicMock(email="test@example.com"))
    service = UserService(mock_uow)
    user_create = UserCreate(email="test@example.com", password="StrongP@ss123")
    with pytest.raises(Exception) as exc_info:
        await service.create_user(user_create)
    assert "already exists" in str(exc_info.value)
