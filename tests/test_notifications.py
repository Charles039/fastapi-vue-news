import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects import mssql

from config.db_conf import AsyncSessionLocal
from crud.notification import _is_unread
from models.favorite import Favorite
from models.news import News
from models.notification import Notification
from models.users import User


def test_unread_condition_uses_valid_sql_server_bit_comparison():
    statement = select(Notification.id).where(_is_unread())
    sql = str(
        statement.compile(
            dialect=mssql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "notification.is_read = 0" in sql
    assert "notification.is_read IS 0" not in sql


@pytest.mark.asyncio
async def test_admin_announcement_reaches_current_users(
    client, db, user_token, admin_token
):
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    forbidden = await client.post(
        "/api/admin/notifications/announcements",
        headers=user_headers,
        json={"title": "维护通知", "content": "今晚进行系统维护。"},
    )
    assert forbidden.status_code == 403

    created = await client.post(
        "/api/admin/notifications/announcements",
        headers=admin_headers,
        json={"title": " 维护通知 ", "content": " 今晚进行系统维护。 "},
    )
    assert created.status_code == 200
    assert created.json()["data"]["recipientCount"] == 2

    for headers in (user_headers, admin_headers):
        listing = await client.get("/api/notifications", headers=headers)
        assert listing.status_code == 200
        assert listing.json()["data"]["total"] == 1
        assert listing.json()["data"]["unreadCount"] == 1
        assert listing.json()["data"]["list"][0]["type"] == "announcement"

    blank = await client.post(
        "/api/admin/notifications/announcements",
        headers=admin_headers,
        json={"title": "   ", "content": "正文"},
    )
    assert blank.status_code == 422


@pytest.mark.asyncio
async def test_notification_read_and_delete_are_user_isolated(
    client, user_token, admin_token
):
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post(
        "/api/admin/notifications/announcements",
        headers=admin_headers,
        json={"title": "公告一", "content": "正文一"},
    )
    await client.post(
        "/api/admin/notifications/announcements",
        headers=admin_headers,
        json={"title": "公告二", "content": "正文二"},
    )

    listing = await client.get(
        "/api/notifications", headers=user_headers, params={"pageSize": 1}
    )
    data = listing.json()["data"]
    assert data["total"] == 2
    assert data["hasMore"] is True
    notification_id = data["list"][0]["id"]

    other_user_cannot_read = await client.patch(
        f"/api/notifications/{notification_id}/read", headers=admin_headers
    )
    assert other_user_cannot_read.status_code == 404

    marked = await client.patch(
        f"/api/notifications/{notification_id}/read", headers=user_headers
    )
    assert marked.status_code == 200
    count = await client.get("/api/notifications/unread-count", headers=user_headers)
    assert count.json()["data"]["unreadCount"] == 1

    marked_all = await client.patch("/api/notifications/read-all", headers=user_headers)
    assert marked_all.status_code == 200
    count = await client.get("/api/notifications/unread-count", headers=user_headers)
    assert count.json()["data"]["unreadCount"] == 0

    other_user_cannot_delete = await client.delete(
        f"/api/notifications/{notification_id}", headers=admin_headers
    )
    assert other_user_cannot_delete.status_code == 404
    deleted = await client.delete(
        f"/api/notifications/{notification_id}", headers=user_headers
    )
    assert deleted.status_code == 200
    missing = await client.delete(
        f"/api/notifications/{notification_id}", headers=user_headers
    )
    assert missing.status_code == 404

    cleared = await client.delete("/api/notifications", headers=user_headers)
    assert cleared.status_code == 200
    assert "1" in cleared.json()["message"]


@pytest.mark.asyncio
async def test_favorite_news_update_is_deduplicated_and_delete_replaces_it(
    client, db, category, news_item, user_token, admin_token
):
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_id = await db.scalar(select(User.id).where(User.username == "reader"))
    db.add(Favorite(user_id=user_id, news_id=news_item.id))
    await db.commit()

    first_update = await client.patch(
        f"/api/admin/news/{news_item.id}",
        headers=admin_headers,
        json={"title": "第一次修改"},
    )
    assert first_update.status_code == 200
    listing = await client.get("/api/notifications", headers=user_headers)
    first_notice = listing.json()["data"]["list"][0]
    assert first_notice["type"] == "news_updated"
    assert first_notice["newsTitle"] == "第一次修改"

    await client.patch(
        f"/api/notifications/{first_notice['id']}/read", headers=user_headers
    )
    second_update = await client.patch(
        f"/api/admin/news/{news_item.id}",
        headers=admin_headers,
        json={"description": "第二次修改"},
    )
    assert second_update.status_code == 200
    listing = await client.get("/api/notifications", headers=user_headers)
    data = listing.json()["data"]
    assert data["total"] == 1
    assert data["unreadCount"] == 1
    assert data["list"][0]["id"] == first_notice["id"]

    deleted = await client.delete(
        f"/api/admin/news/{news_item.id}", headers=admin_headers
    )
    assert deleted.status_code == 200
    listing = await client.get("/api/notifications", headers=user_headers)
    data = listing.json()["data"]
    assert data["total"] == 1
    assert data["list"][0]["type"] == "news_deleted"
    assert data["list"][0]["newsTitle"] == "第一次修改"
    assert await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.type == "news_updated"
        )
    ) == 0


@pytest.mark.asyncio
async def test_news_update_rolls_back_when_notification_write_fails(
    client, db, news_item, user_token, admin_token, monkeypatch
):
    user_id = await db.scalar(select(User.id).where(User.username == "reader"))
    db.add(Favorite(user_id=user_id, news_id=news_item.id))
    await db.commit()

    async def fail_notification(*_args, **_kwargs):
        raise RuntimeError("notification write failed")

    monkeypatch.setattr("crud.news.notify_favorited_news_updated", fail_notification)
    response = await client.patch(
        f"/api/admin/news/{news_item.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "不应保存的标题"},
    )
    assert response.status_code == 500

    async with AsyncSessionLocal() as verification_db:
        stored_title = await verification_db.scalar(
            select(News.title).where(News.id == news_item.id)
        )
    assert stored_title == "测试新闻"
