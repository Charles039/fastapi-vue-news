import asyncio
import os
from unittest.mock import AsyncMock

import pytest

from cache import news_cache
from config import cache_conf
from crud import news


@pytest.mark.asyncio
async def test_cache_json_version_and_lock(isolated_services):
    assert await cache_conf.get_json_cache("missing") is None
    assert await cache_conf.set_cache("json", {"value": "中文"}, expire=30)
    assert await cache_conf.get_json_cache("json") == {"value": "中文"}

    assert await news_cache.get_news_list_version(7) == 0
    assert await news_cache.invalidate_news_category(7) == 1
    assert await news_cache.get_news_list_version(7) == 1
    assert news_cache.build_news_page_key(7, 2, 10, 1).endswith("page:2:size:10")

    key, token = await news_cache.acquire_news_page_lock(7, 1, 10, 1)
    assert token
    assert await news_cache.acquire_news_page_lock(7, 1, 10, 1) == (key, False)


@pytest.mark.asyncio
async def test_complete_page_cache_hits_database_once(monkeypatch):
    expected = {"list": [], "total": 0, "hasMore": False}
    query = AsyncMock(return_value=expected)
    monkeypatch.setattr(news, "_query_news_page", query)
    monkeypatch.setattr(news, "release_news_page_lock", AsyncMock(return_value=True))

    first = await news.get_news_page(object(), 1, 1, 10)
    second = await news.get_news_page(object(), 1, 1, 10)
    assert first == expected
    assert second == expected
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_stampede_lock_makes_concurrent_requests_share_result(monkeypatch):
    async def slow_query(*args):
        await asyncio.sleep(0.1)
        return {"list": [{"id": 1}], "total": 1, "hasMore": False}

    query = AsyncMock(side_effect=slow_query)
    monkeypatch.setattr(news, "_query_news_page", query)
    monkeypatch.setattr(news, "release_news_page_lock", AsyncMock(return_value=True))

    results = await asyncio.gather(
        *(news.get_news_page(object(), 3, 1, 10) for _ in range(6))
    )
    assert all(result == results[0] for result in results)
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_failure_degrades_to_database(monkeypatch):
    expected = {"list": [{"id": 9}], "total": 1, "hasMore": False}
    query = AsyncMock(return_value=expected)
    monkeypatch.setattr(news, "_query_news_page", query)
    monkeypatch.setattr(news, "get_news_list_version", AsyncMock(return_value=0))
    monkeypatch.setattr(news, "get_cached_news_page", AsyncMock(return_value=None))
    monkeypatch.setattr(
        news, "acquire_news_page_lock", AsyncMock(return_value=("lock:key", None))
    )

    assert await news.get_news_page(object(), 9, 1, 10) == expected
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_memory_cache_backend(monkeypatch):
    monkeypatch.setattr(cache_conf, "CACHE_BACKEND", "memory")
    cache_conf.clear_memory_cache()

    assert await cache_conf.get_cache("missing") is None
    assert await cache_conf.set_cache("demo", {"value": "ok"}, expire=30)
    assert await cache_conf.get_json_cache("demo") == {"value": "ok"}
    assert await cache_conf.increment_cache("version") == 1
    assert await cache_conf.increment_cache("version") == 2

    token = await cache_conf.acquire_lock("demo-lock", expire=30)
    assert token
    assert await cache_conf.acquire_lock("demo-lock", expire=30) is False
    assert await cache_conf.release_lock("demo-lock", "wrong-token") is False
    assert await cache_conf.release_lock("demo-lock", token) is True


@pytest.mark.redis_integration
@pytest.mark.asyncio
async def test_real_redis_round_trip():
    if os.getenv("RUN_REDIS_INTEGRATION") != "1":
        pytest.skip("set RUN_REDIS_INTEGRATION=1 to test a real Redis instance")

    key = "test:news-cache:integration"
    await cache_conf.redis_client.set(key, "ok", ex=10)
    try:
        assert await cache_conf.redis_client.get(key) == "ok"
    finally:
        await cache_conf.redis_client.delete(key)
