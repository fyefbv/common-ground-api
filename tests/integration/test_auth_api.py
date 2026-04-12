import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    reg_resp = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "StrongP@ss123"},
    )
    assert reg_resp.status_code == 201
    tokens = reg_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "StrongP@ss123"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    bad_login = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "wrong"}
    )
    assert bad_login.status_code == 401
