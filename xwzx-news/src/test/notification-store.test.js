import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import axios from 'axios'

import { useNotificationStore } from '../store/modules/notification'
import { useUserStore } from '../store/user'


vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('notification store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useUserStore().token = 'reader-token'
    vi.clearAllMocks()
  })

  it('loads unread count and appends paginated notifications', async () => {
    axios.get
      .mockResolvedValueOnce({ data: { data: { unreadCount: 3 } } })
      .mockResolvedValueOnce({
        data: { data: { list: [{ id: 1, isRead: false }], total: 2, hasMore: true, unreadCount: 2 } },
      })
      .mockResolvedValueOnce({
        data: { data: { list: [{ id: 2, isRead: true }], total: 2, hasMore: false, unreadCount: 1 } },
      })
    const store = useNotificationStore()

    expect((await store.fetchUnreadCount()).unreadCount).toBe(3)
    expect((await store.fetchNotifications()).success).toBe(true)
    expect((await store.fetchNotifications(2)).success).toBe(true)
    expect(store.notifications.map((item) => item.id)).toEqual([1, 2])
    expect(store.page).toBe(2)
    expect(store.total).toBe(2)
    expect(store.hasMore).toBe(false)
    expect(store.unreadCount).toBe(1)
    expect(store.loading).toBe(false)
    expect(axios.get).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/notifications'),
      { headers: { Authorization: 'Bearer reader-token' }, params: { page: 2, pageSize: 20 } },
    )
  })

  it('marks one or all notifications as read', async () => {
    axios.patch.mockResolvedValue({ data: { code: 200 } })
    const store = useNotificationStore()
    store.notifications = [{ id: 1, isRead: false }, { id: 2, isRead: true }]
    store.unreadCount = 1

    expect((await store.markRead(1)).success).toBe(true)
    expect(store.notifications[0].isRead).toBe(true)
    expect(store.unreadCount).toBe(0)
    expect((await store.markRead(2)).success).toBe(true)
    expect(axios.patch).toHaveBeenCalledTimes(1)

    store.notifications[0].isRead = false
    store.unreadCount = 1
    expect((await store.markAllRead()).success).toBe(true)
    expect(store.notifications.every((item) => item.isRead)).toBe(true)
    expect(store.unreadCount).toBe(0)
  })

  it('deletes one notification and clears the remaining list', async () => {
    axios.delete.mockResolvedValue({ data: { code: 200 } })
    const store = useNotificationStore()
    store.notifications = [{ id: 1, isRead: false }, { id: 2, isRead: true }]
    store.total = 2
    store.unreadCount = 1
    store.hasMore = true

    expect((await store.deleteNotification(1)).success).toBe(true)
    expect(store.notifications).toEqual([{ id: 2, isRead: true }])
    expect(store.total).toBe(1)
    expect(store.unreadCount).toBe(0)

    expect((await store.clearNotifications()).success).toBe(true)
    expect(store.notifications).toEqual([])
    expect(store.total).toBe(0)
    expect(store.hasMore).toBe(false)
  })

  it('publishes an announcement with administrator bearer auth', async () => {
    axios.post.mockResolvedValue({ data: { data: { recipientCount: 9 } } })
    const store = useNotificationStore()

    const result = await store.publishAnnouncement({ title: '公告', content: '正文' })
    expect(result).toEqual({ success: true, data: { recipientCount: 9 } })
    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/admin/notifications/announcements'),
      { title: '公告', content: '正文' },
      { headers: { Authorization: 'Bearer reader-token' } },
    )
  })

  it('uses safe defaults for empty responses and network errors', async () => {
    axios.get
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ data: {} })
      .mockRejectedValueOnce(new Error('network down'))
    const store = useNotificationStore()
    store.notifications = [{ id: 99 }]
    store.unreadCount = 4

    expect((await store.fetchUnreadCount()).unreadCount).toBe(0)
    expect((await store.fetchNotifications()).success).toBe(true)
    expect(store.notifications).toEqual([])
    expect(store.total).toBe(0)
    expect(store.unreadCount).toBe(0)
    expect(await store.fetchUnreadCount()).toEqual({
      success: false,
      status: undefined,
      message: '获取未读通知数量失败',
    })
  })

  it('does not reduce unread count when deleting a read item', async () => {
    axios.delete.mockResolvedValue({ data: { code: 200 } })
    const store = useNotificationStore()
    store.notifications = [{ id: 1, isRead: true }]
    store.total = 0
    store.unreadCount = 2

    expect((await store.deleteNotification(1)).success).toBe(true)
    expect(store.unreadCount).toBe(2)
    expect(store.total).toBe(0)
  })

  it.each([
    ['fetchUnreadCount', () => useNotificationStore().fetchUnreadCount()],
    ['fetchNotifications', () => useNotificationStore().fetchNotifications()],
    ['markRead', () => useNotificationStore().markRead(1)],
    ['markAllRead', () => useNotificationStore().markAllRead()],
    ['deleteNotification', () => useNotificationStore().deleteNotification(1)],
    ['clearNotifications', () => useNotificationStore().clearNotifications()],
    ['publishAnnouncement', () => useNotificationStore().publishAnnouncement({})],
  ])('returns backend errors when %s fails', async (_name, action) => {
    const failure = { response: { status: 403, data: { message: '无权限' } } }
    axios.get.mockRejectedValueOnce(failure)
    axios.patch.mockRejectedValueOnce(failure)
    axios.delete.mockRejectedValueOnce(failure)
    axios.post.mockRejectedValueOnce(failure)

    expect(await action()).toMatchObject({ success: false, status: 403, message: '无权限' })
  })
})
