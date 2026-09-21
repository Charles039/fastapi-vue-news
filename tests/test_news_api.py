import pytest
from sqlalchemy import func, select

from models.favorite import Favorite
from models.history import History
from models.news import News


@pytest.mark.asyncio
async def test_public_news_endpoints(client, category, news_item):
    categories = await client.get("/api/news/categories")
    assert categories.status_code == 200
    assert categories.json()["data"][0]["name"] == "科技"

    first = await client.get(
        "/api/news/list",
        params={"categoryId": category.id, "page": 1, "pageSize": 10},
    )
    assert first.status_code == 200
    assert first.json()["data"]["total"] == 1
    assert first.json()["data"]["hasMore"] is False

    second = await client.get(
        "/api/news/list",
        params={"categoryId": category.id, "page": 1, "pageSize": 10},
    )
    assert second.json() == first.json()

    detail = await client.get("/api/news/detail", params={"id": news_item.id})
    assert detail.status_code == 200
    assert detail.json()["data"]["title"] == "测试新闻"

    missing = await client.get("/api/news/detail", params={"id": 99999})
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_admin_auth_and_crud(
    client, db, category, second_category, user_token, admin_token
):
    ordinary_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "title": "管理员新增",
        "description": "简介",
        "content": "正文",
        "categoryId": category.id,
        "author": "管理员",
    }

    forbidden = await client.post(
        "/api/admin/news", headers=ordinary_headers, json=payload
    )
    assert forbidden.status_code == 403

    invalid_category = await client.post(
        "/api/admin/news",
        headers=admin_headers,
        json={**payload, "categoryId": 99999},
    )
    assert invalid_category.status_code == 400

    created = await client.post(
        "/api/admin/news", headers=admin_headers, json=payload
    )
    assert created.status_code == 200
    created_data = created.json()["data"]
    news_id = created_data["id"]

    empty_patch = await client.patch(
        f"/api/admin/news/{news_id}", headers=admin_headers, json={}
    )
    assert empty_patch.status_code == 422

    invalid_patch = await client.patch(
        f"/api/admin/news/{news_id}",
        headers=admin_headers,
        json={"categoryId": 99999},
    )
    assert invalid_patch.status_code == 400

    updated = await client.patch(
        f"/api/admin/news/{news_id}",
        headers=admin_headers,
        json={"title": "局部修改后", "categoryId": second_category.id},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["title"] == "局部修改后"
    assert updated.json()["data"]["content"] == "正文"

    # 删除新闻必须连同收藏与历史记录一起清理。
    db.add(Favorite(user_id=1, news_id=news_id))
    db.add(History(user_id=1, news_id=news_id))
    await db.commit()

    deleted = await client.delete(
        f"/api/admin/news/{news_id}", headers=admin_headers
    )
    assert deleted.status_code == 200
    assert await db.scalar(select(func.count(Favorite.id))) == 0
    assert await db.scalar(select(func.count(History.id))) == 0
    assert await db.get(News, news_id) is None

    missing_update = await client.patch(
        "/api/admin/news/99999", headers=admin_headers, json={"title": "不存在"}
    )
    assert missing_update.status_code == 404
    missing_delete = await client.delete(
        "/api/admin/news/99999", headers=admin_headers
    )
    assert missing_delete.status_code == 404

