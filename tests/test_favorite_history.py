import pytest


@pytest.mark.asyncio
async def test_favorite_lifecycle(client, user_token, news_item):
    headers = {"Authorization": f"Bearer {user_token}"}

    initial = await client.get(
        "/api/favorite/check", headers=headers, params={"newsId": news_item.id}
    )
    assert initial.json()["data"]["isFavorite"] is False

    added = await client.post(
        "/api/favorite/add", headers=headers, json={"newsId": news_item.id}
    )
    assert added.status_code == 200

    checked = await client.get(
        "/api/favorite/check", headers=headers, params={"newsId": news_item.id}
    )
    assert checked.json()["data"]["isFavorite"] is True

    listing = await client.get("/api/favorite/list", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] == 1
    assert listing.json()["data"]["list"][0]["id"] == news_item.id

    removed = await client.delete(
        "/api/favorite/remove", headers=headers, params={"newsId": news_item.id}
    )
    assert removed.status_code == 200
    missing = await client.delete(
        "/api/favorite/remove", headers=headers, params={"newsId": news_item.id}
    )
    assert missing.status_code == 404

    await client.post(
        "/api/favorite/add", headers=headers, json={"newsId": news_item.id}
    )
    cleared = await client.delete("/api/favorite/clear", headers=headers)
    assert cleared.status_code == 200
    assert "1" in cleared.json()["message"]


@pytest.mark.asyncio
async def test_history_lifecycle(client, user_token, news_item):
    headers = {"Authorization": f"Bearer {user_token}"}

    added = await client.post(
        "/api/history/add", headers=headers, json={"newsId": news_item.id}
    )
    assert added.status_code == 200
    # 再次浏览应更新原记录，而不是新增重复行。
    repeated = await client.post(
        "/api/history/add", headers=headers, json={"newsId": news_item.id}
    )
    assert repeated.status_code == 200

    listing = await client.get("/api/history/list", headers=headers)
    assert listing.status_code == 200
    data = listing.json()["data"]
    assert data["total"] == 1
    history_id = data["list"][0]["historyId"]

    deleted = await client.delete(
        f"/api/history/delete/{history_id}", headers=headers
    )
    assert deleted.status_code == 200
    missing = await client.delete(
        f"/api/history/delete/{history_id}", headers=headers
    )
    assert missing.status_code == 404

    await client.post(
        "/api/history/add", headers=headers, json={"newsId": news_item.id}
    )
    cleared = await client.delete("/api/history/clear", headers=headers)
    assert cleared.status_code == 200

