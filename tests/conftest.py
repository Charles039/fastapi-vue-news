import os

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["SQL_ECHO"] = "false"
os.environ["DEBUG_MODE"] = "false"

from config import cache_conf  # noqa: E402
from config.db_conf import AsyncSessionLocal, async_engine  # noqa: E402
from main import app  # noqa: E402
from models.base import Base  # noqa: E402
from models.favorite import Favorite  # noqa: F401,E402
from models.history import History  # noqa: F401,E402
from models.news import Category, News  # noqa: E402
from models.notification import Notification  # noqa: F401,E402
from models.users import User, UserToken  # noqa: F401,E402


@pytest_asyncio.fixture(autouse=True)
async def isolated_services(request, monkeypatch):
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    is_real_redis_test = (
        request.node.get_closest_marker("redis_integration") is not None
        and os.getenv("RUN_REDIS_INTEGRATION") == "1"
    )
    if is_real_redis_test:
        yield cache_conf.redis_client
    else:
        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(cache_conf, "redis_client", fake_redis)
        yield fake_redis
        await fake_redis.aclose()


@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest_asyncio.fixture
async def category(db):
    item = Category(name="科技", sort_order=1)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@pytest_asyncio.fixture
async def second_category(db):
    item = Category(name="体育", sort_order=2)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@pytest_asyncio.fixture
async def news_item(db, category):
    item = News(
        title="测试新闻",
        description="测试简介",
        content="测试正文",
        author="测试作者",
        category_id=category.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def register(client, username="reader", password="password123"):
    response = await client.post(
        "/api/user/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["token"]


@pytest_asyncio.fixture
async def user_token(client):
    return await register(client)


@pytest_asyncio.fixture
async def admin_token(client, db):
    token = await register(client, username="admin")
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one()
    admin.is_admin = True
    await db.commit()
    return token
