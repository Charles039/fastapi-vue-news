import pytest

from models.base import Base
from utils.security import verify_password


@pytest.mark.asyncio
async def test_shared_base_contains_every_table():
    assert set(Base.metadata.tables) == {
        "user",
        "user_token",
        "news_category",
        "news",
        "favorite",
        "history",
        "notification",
    }


@pytest.mark.asyncio
async def test_register_login_and_info(client):
    register = await client.post(
        "/api/user/register",
        json={"username": "alice", "password": "secret123"},
    )
    assert register.status_code == 200
    payload = register.json()
    assert payload["data"]["userInfo"]["isAdmin"] is False
    token = payload["data"]["token"]

    duplicate = await client.post(
        "/api/user/register",
        json={"username": "alice", "password": "secret123"},
    )
    assert duplicate.status_code == 400

    wrong_password = await client.post(
        "/api/user/login",
        json={"username": "alice", "password": "wrong"},
    )
    assert wrong_password.status_code == 401

    login = await client.post(
        "/api/user/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["token"]

    info = await client.get(
        "/api/user/info", headers={"Authorization": f"Bearer {token}"}
    )
    assert info.status_code == 200
    assert info.json()["data"]["username"] == "alice"

    invalid = await client.get(
        "/api/user/info", headers={"Authorization": "Bearer invalid"}
    )
    assert invalid.status_code == 401


@pytest.mark.asyncio
async def test_profile_and_password_updates(client, user_token):
    headers = {"Authorization": user_token}
    update = await client.put(
        "/api/user/update",
        headers=headers,
        json={"nickname": "新昵称", "bio": "新的简介"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["nickname"] == "新昵称"

    wrong = await client.put(
        "/api/user/password",
        headers=headers,
        json={"oldPassword": "bad", "newPassword": "newpass123"},
    )
    assert wrong.status_code == 500

    changed = await client.put(
        "/api/user/password",
        headers=headers,
        json={"oldPassword": "password123", "newPassword": "newpass123"},
    )
    assert changed.status_code == 200

    login = await client.post(
        "/api/user/login",
        json={"username": "reader", "password": "newpass123"},
    )
    assert login.status_code == 200


def test_password_hash_is_not_plaintext():
    from utils.security import get_hash_password

    hashed = get_hash_password("password123")
    assert hashed != "password123"
    assert verify_password("password123", hashed)
