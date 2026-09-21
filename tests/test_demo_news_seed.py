import json
from datetime import datetime

import pytest
from sqlalchemy import func, select

from models.news import Category, News
from scripts.seed_demo_news import load_demo_document, seed_demo_news


def write_demo_file(path, news):
    path.write_text(
        json.dumps({"version": 1, "news": news}, ensure_ascii=False),
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_seed_demo_news_is_repeatable_and_preserves_fields(
    tmp_path, db, category, monkeypatch
):
    data_path = tmp_path / "demo_news.json"
    write_demo_file(
        data_path,
        [
            {
                "category": category.name,
                "title": "演示新闻",
                "description": "演示简介",
                "content": "完整演示正文",
                "image": "https://example.com/demo.jpg",
                "author": "演示作者",
                "views": 321,
                "publishTime": "2026-09-15T10:30:00",
            },
            {
                "category": category.name,
                "title": "演示新闻",
                "description": "输入文件内重复",
                "content": "不应重复导入",
                "views": 1,
                "publishTime": "2026-09-15T11:30:00",
            },
        ],
    )
    invalidated = []

    async def record_invalidation(category_id):
        invalidated.append(category_id)
        return 1

    monkeypatch.setattr(
        "scripts.seed_demo_news.invalidate_news_category", record_invalidation
    )

    first = await seed_demo_news(data_path)
    second = await seed_demo_news(data_path)

    assert first.inserted == 1
    assert first.skipped == 1
    assert second.inserted == 0
    assert second.skipped == 2
    assert invalidated == [category.id]

    stored = await db.scalar(select(News).where(News.title == "演示新闻"))
    assert stored.description == "演示简介"
    assert stored.content == "完整演示正文"
    assert stored.image == "https://example.com/demo.jpg"
    assert stored.author == "演示作者"
    assert stored.views == 321
    assert stored.publish_time == datetime(2026, 9, 15, 10, 30)


@pytest.mark.asyncio
async def test_seed_rejects_missing_category_without_writing(tmp_path, db):
    data_path = tmp_path / "demo_news.json"
    write_demo_file(
        data_path,
        [
            {
                "category": "科技",
                "title": "不能导入",
                "content": "正文",
                "publishTime": "2026-09-15T10:30:00",
            }
        ],
    )

    with pytest.raises(ValueError, match="数据库缺少新闻分类"):
        await seed_demo_news(data_path)

    assert await db.scalar(select(func.count(News.id))) == 0


def test_load_demo_document_rejects_empty_and_invalid_data(tmp_path):
    empty_path = tmp_path / "empty.json"
    write_demo_file(empty_path, [])
    assert load_demo_document(empty_path).news == []

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text('{"news": [{"title": "缺少字段"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="演示数据格式不正确"):
        load_demo_document(invalid_path)
