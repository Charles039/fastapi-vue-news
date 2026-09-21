<template>
  <div class="notification-page">
    <van-nav-bar title="消息通知" left-text="返回" left-arrow fixed @click-left="router.back()" />

    <div class="notification-actions">
      <van-button size="small" :disabled="!store.unreadCount" @click="markAllRead">全部已读</van-button>
      <van-button size="small" type="danger" plain :disabled="!store.total" @click="clearAll">清空全部</van-button>
    </div>

    <van-empty v-if="!store.loading && !store.notifications.length" description="暂无通知" />
    <van-list
      v-else
      v-model:loading="loadingMore"
      :finished="!store.hasMore"
      finished-text="没有更多通知了"
      @load="loadMore"
    >
      <div
        v-for="item in store.notifications"
        :key="item.id"
        class="notification-card"
        :class="{ unread: !item.isRead }"
        @click="openNotification(item)"
      >
        <div class="notification-heading">
          <span v-if="!item.isRead" class="unread-dot"></span>
          <strong>{{ item.title }}</strong>
          <span class="notification-time">{{ formatTime(item.updatedAt) }}</span>
        </div>
        <p>{{ item.content }}</p>
        <div class="notification-footer">
          <span>{{ typeLabel(item.type) }}</span>
          <van-button size="mini" type="danger" plain @click.stop="removeItem(item)">删除</van-button>
        </div>
      </div>
    </van-list>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showDialog, showFailToast, showSuccessToast } from 'vant'

import { useNotificationStore } from '../store/modules/notification'

const router = useRouter()
const store = useNotificationStore()
const loadingMore = ref(false)

const typeLabel = (type) => ({
  announcement: '系统公告',
  news_updated: '新闻更新',
  news_deleted: '新闻删除',
}[type] || '系统通知')

const formatTime = (value) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : ''

const loadFirstPage = async () => {
  const result = await store.fetchNotifications(1)
  if (!result.success) showFailToast(result.message)
}

const loadMore = async () => {
  if (!store.hasMore) {
    loadingMore.value = false
    return
  }
  const result = await store.fetchNotifications(store.page + 1)
  loadingMore.value = false
  if (!result.success) showFailToast(result.message)
}

const openNotification = async (item) => {
  const result = await store.markRead(item.id)
  if (!result.success) {
    showFailToast(result.message)
    return
  }
  if (item.type === 'news_updated' && item.newsId) {
    router.push(`/news/detail/${item.newsId}`)
    return
  }
  showDialog({ title: item.title, message: item.content })
}

const markAllRead = async () => {
  const result = await store.markAllRead()
  if (result.success) showSuccessToast('已全部标记为已读')
  else showFailToast(result.message)
}

const removeItem = async (item) => {
  try {
    await showConfirmDialog({ title: '确定删除', message: `确定删除“${item.title}”吗？` })
    const result = await store.deleteNotification(item.id)
    if (!result.success) showFailToast(result.message)
  } catch {
    // 用户取消删除。
  }
}

const clearAll = async () => {
  try {
    await showConfirmDialog({ title: '确定清空', message: '确定清空全部通知吗？' })
    const result = await store.clearNotifications()
    if (result.success) showSuccessToast('通知已清空')
    else showFailToast(result.message)
  } catch {
    // 用户取消清空。
  }
}

onMounted(loadFirstPage)
</script>

<style scoped>
.notification-page { min-height: 100vh; box-sizing: border-box; padding: 62px 16px 28px; background: var(--background-color); color: var(--text-color); }
.notification-actions { display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 14px; }
.notification-card { margin-bottom: 12px; padding: 14px; border-radius: 10px; background: #fff; box-shadow: 0 2px 10px rgb(0 0 0 / 6%); }
.notification-card.unread { border-left: 4px solid var(--primary-color); }
.notification-heading { display: flex; align-items: center; gap: 7px; }
.unread-dot { width: 8px; height: 8px; border-radius: 50%; background: #ee0a24; flex: none; }
.notification-time { margin-left: auto; color: #969799; font-size: 12px; }
.notification-card p { margin: 10px 0; color: #646566; line-height: 1.6; white-space: pre-wrap; }
.notification-footer { display: flex; align-items: center; justify-content: space-between; color: #969799; font-size: 12px; }
</style>

