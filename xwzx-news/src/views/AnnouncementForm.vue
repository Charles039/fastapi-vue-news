<template>
  <div class="announcement-page">
    <van-nav-bar title="发布公告" left-text="返回" left-arrow fixed @click-left="router.back()" />
    <van-form class="announcement-form" @submit="submit">
      <van-cell-group inset>
        <van-field
          v-model="title"
          label="公告标题"
          maxlength="100"
          show-word-limit
          placeholder="请输入公告标题"
          :rules="[{ required: true, message: '请输入公告标题' }]"
        />
        <van-field
          v-model="content"
          label="公告正文"
          type="textarea"
          rows="8"
          autosize
          maxlength="5000"
          show-word-limit
          placeholder="请输入公告正文"
          :rules="[{ required: true, message: '请输入公告正文' }]"
        />
      </van-cell-group>
      <div class="submit-area">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          发布给全部用户
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast, showSuccessToast } from 'vant'

import { useNotificationStore } from '../store/modules/notification'

const router = useRouter()
const store = useNotificationStore()
const title = ref('')
const content = ref('')
const submitting = ref(false)

const submit = async () => {
  submitting.value = true
  try {
    const result = await store.publishAnnouncement({
      title: title.value.trim(),
      content: content.value.trim(),
    })
    if (!result.success) {
      if (result.status === 401 || result.status === 403) {
        showFailToast('无管理员权限')
        router.replace('/my')
        return
      }
      showFailToast(result.message)
      return
    }
    showSuccessToast(`公告已发送给 ${result.data?.recipientCount || 0} 位用户`)
    router.replace('/my')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.announcement-page { min-height: 100vh; background: var(--background-color); }
.announcement-form { padding-top: 62px; padding-bottom: 28px; }
.submit-area { margin: 22px 16px; }
</style>

