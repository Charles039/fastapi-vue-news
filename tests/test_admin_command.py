import pytest
from sqlalchemy import select

from models.users import User
from scripts import create_admin
from utils.security import get_hash_password, verify_password


@pytest.mark.asyncio
async def test_create_admin_interactively(monkeypatch, db):
    monkeypatch.setattr("builtins.input", lambda _prompt: "first-admin")
    passwords = iter(["secure123", "secure123"])
    monkeypatch.setattr(create_admin, "getpass", lambda _prompt: next(passwords))

    assert await create_admin.create_or_promote_admin() == 0
    result = await db.execute(select(User).where(User.username == "first-admin"))
    admin = result.scalar_one()
    assert admin.is_admin is True
    assert verify_password("secure123", admin.password)


@pytest.mark.asyncio
async def test_promote_existing_user_without_changing_password(monkeypatch, db):
    original_hash = get_hash_password("original-password")
    db.add(User(username="existing", password=original_hash, is_admin=False))
    await db.commit()
    monkeypatch.setattr("builtins.input", lambda _prompt: "existing")
    monkeypatch.setattr(
        create_admin,
        "getpass",
        lambda _prompt: pytest.fail("existing users must not be prompted for a password"),
    )

    assert await create_admin.create_or_promote_admin() == 0
    result = await db.execute(select(User).where(User.username == "existing"))
    admin = result.scalar_one()
    assert admin.is_admin is True
    assert admin.password == original_hash


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("username", "passwords"),
    [
        ("", []),
        ("new-admin", ["short", "short"]),
        ("new-admin", ["secure123", "different123"]),
    ],
)
async def test_reject_invalid_admin_input(monkeypatch, username, passwords):
    monkeypatch.setattr("builtins.input", lambda _prompt: username)
    password_values = iter(passwords)
    monkeypatch.setattr(create_admin, "getpass", lambda _prompt: next(password_values))

    assert await create_admin.create_or_promote_admin() == 1

