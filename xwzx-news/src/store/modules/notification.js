import { defineStore } from 'pinia'
import axios from 'axios'

import { apiConfig } from '../../config/api'
import { useUserStore } from '../user'


const requestError = (error, fallback) => ({
  success: false,
  status: error.response?.status,
  message: error.response?.data?.message || fallback,
})

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [],
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: false,
    unreadCount: 0,
    loading: false,
  }),

  actions: {
    authHeaders() {
      const userStore = useUserStore()
      return { Authorization: `Bearer ${userStore.token}` }
    },

    async fetchUnreadCount() {
      try {
        const response = await axios.get(
          `${apiConfig.baseURL}/api/notifications/unread-count`,
          { headers: this.authHeaders() },
        )
        this.unreadCount = response.data?.data?.unreadCount || 0
        return { success: true, unreadCount: this.unreadCount }
      } catch (error) {
        return requestError(error, '获取未读通知数量失败')
      }
    },

    async fetchNotifications(page = 1) {
      this.loading = true
      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/notifications`, {
          headers: this.authHeaders(),
          params: { page, pageSize: this.pageSize },
        })
        const data = response.data?.data || {}
        const items = data.list || []
        this.notifications = page === 1 ? items : [...this.notifications, ...items]
        this.page = page
        this.total = data.total || 0
        this.hasMore = Boolean(data.hasMore)
        this.unreadCount = data.unreadCount || 0
        return { success: true }
      } catch (error) {
        return requestError(error, '获取通知列表失败')
      } finally {
        this.loading = false
      }
    },

    async markRead(notificationId) {
      const item = this.notifications.find((notice) => notice.id === notificationId)
      if (item?.isRead) return { success: true }
      try {
        await axios.patch(
          `${apiConfig.baseURL}/api/notifications/${notificationId}/read`,
          {},
          { headers: this.authHeaders() },
        )
        if (item) item.isRead = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
        return { success: true }
      } catch (error) {
        return requestError(error, '标记通知已读失败')
      }
    },

    async markAllRead() {
      try {
        await axios.patch(
          `${apiConfig.baseURL}/api/notifications/read-all`,
          {},
          { headers: this.authHeaders() },
        )
        this.notifications.forEach((item) => { item.isRead = true })
        this.unreadCount = 0
        return { success: true }
      } catch (error) {
        return requestError(error, '全部标记已读失败')
      }
    },

    async deleteNotification(notificationId) {
      try {
        await axios.delete(`${apiConfig.baseURL}/api/notifications/${notificationId}`, {
          headers: this.authHeaders(),
        })
        const item = this.notifications.find((notice) => notice.id === notificationId)
        if (item && !item.isRead) this.unreadCount = Math.max(0, this.unreadCount - 1)
        this.notifications = this.notifications.filter((notice) => notice.id !== notificationId)
        this.total = Math.max(0, this.total - 1)
        return { success: true }
      } catch (error) {
        return requestError(error, '删除通知失败')
      }
    },

    async clearNotifications() {
      try {
        await axios.delete(`${apiConfig.baseURL}/api/notifications`, {
          headers: this.authHeaders(),
        })
        this.notifications = []
        this.total = 0
        this.hasMore = false
        this.unreadCount = 0
        return { success: true }
      } catch (error) {
        return requestError(error, '清空通知失败')
      }
    },

    async publishAnnouncement(payload) {
      try {
        const response = await axios.post(
          `${apiConfig.baseURL}/api/admin/notifications/announcements`,
          payload,
          { headers: this.authHeaders() },
        )
        return { success: true, data: response.data?.data }
      } catch (error) {
        return requestError(error, '发布公告失败')
      }
    },
  },
})

