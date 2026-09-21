<template>
  <div class="admin-form-page">
    <van-nav-bar
      :title="isEdit ? '编辑新闻' : '新增新闻'"
      left-text="返回"
      left-arrow
      fixed
      @click-left="router.back()"
    />

    <van-form class="news-form" @submit="submit">
      <van-cell-group inset>
        <van-field
          v-model="form.title"
          name="title"
          label="标题"
          placeholder="请输入新闻标题"
          maxlength="255"
          show-word-limit
          :rules="[{ required: true, message: '请输入新闻标题' }]"
        />
        <van-field
          v-model="form.description"
          name="description"
          label="简介"
          type="textarea"
          rows="2"
          autosize
          maxlength="500"
          show-word-limit
          placeholder="请输入新闻简介（可选）"
        />
        <van-field
          v-model="form.content"
          name="content"
          label="正文"
          type="textarea"
          rows="8"
          autosize
          placeholder="请输入新闻正文"
          :rules="[{ required: true, message: '请输入新闻正文' }]"
        />
        <van-field v-model="form.image" name="image" label="图片 URL" placeholder="https://example.com/image.jpg" />
        <div v-if="form.image" class="image-preview">
          <img :src="form.image" alt="封面预览" @error="imageFailed = true" @load="imageFailed = false" />
          <span v-if="imageFailed">图片无法加载，请检查 URL</span>
        </div>
        <van-field v-model="form.author" name="author" label="作者" maxlength="50" placeholder="请输入作者（可选）" />
        <div class="native-field">
          <label for="news-category">分类</label>
          <select id="news-category" v-model.number="form.categoryId" required>
            <option disabled :value="null">请选择分类</option>
            <option v-for="category in store.categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
        </div>
        <van-field
          v-model="form.publishTime"
          name="publishTime"
          label="发布时间"
          type="datetime-local"
          placeholder="留空则使用当前时间"
        />
      </van-cell-group>

      <div class="submit-area">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          {{ isEdit ? '保存修改' : '发布新闻' }}
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showSuccessToast, showToast } from 'vant'

import { useAdminNewsStore } from '../store/modules/adminNews'

const route = useRoute()
const router = useRouter()
const store = useAdminNewsStore()
const isEdit = computed(() => route.name === 'AdminNewsEdit')
const submitting = ref(false)
const imageFailed = ref(false)
const original = ref(null)

const form = reactive({
  title: '',
  description: '',
  content: '',
  image: '',
  author: '',
  categoryId: null,
  publishTime: '',
})

const toDateTimeLocal = (value) => value ? String(value).replace(' ', 'T').slice(0, 16) : ''

const fillForm = (item) => {
  form.title = item.title || ''
  form.description = item.description || ''
  form.content = item.content || ''
  form.image = item.image || ''
  form.author = item.author || ''
  form.categoryId = Number(item.categoryId ?? item.category_id)
  form.publishTime = toDateTimeLocal(item.publishTime ?? item.publish_time)
  original.value = buildPayload()
}

const buildPayload = () => {
  const payload = {
    title: form.title.trim(),
    description: form.description.trim() || null,
    content: form.content.trim(),
    image: form.image.trim() || null,
    author: form.author.trim() || null,
    categoryId: Number(form.categoryId),
  }
  if (form.publishTime) payload.publishTime = form.publishTime
  return payload
}

const handleFailure = (result) => {
  if (result.status === 401 || result.status === 403) {
    showFailToast('无管理员权限')
    router.replace('/my')
    return
  }
  showFailToast(result.message || '保存失败')
}

const submit = async () => {
  if (!form.categoryId) {
    showToast('请选择新闻分类')
    return
  }

  submitting.value = true
  try {
    const payload = buildPayload()
    let result
    if (isEdit.value) {
      const changes = Object.fromEntries(
        Object.entries(payload).filter(([key, value]) => original.value?.[key] !== value),
      )
      if (!Object.keys(changes).length) {
        showToast('没有需要保存的修改')
        return
      }
      result = await store.updateNews(route.params.id, changes)
    } else {
      result = await store.createNews(payload)
    }

    if (!result.success) {
      handleFailure(result)
      return
    }

    sessionStorage.removeItem('admin-news-edit')
    showSuccessToast(isEdit.value ? '修改新闻成功' : '新增新闻成功')
    store.currentCategoryId = result.data.categoryId || payload.categoryId
    router.replace('/admin/news')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (!store.categories.length) {
    const result = await store.fetchCategories()
    if (!result.success) {
      showFailToast(result.message)
      return
    }
  }

  if (isEdit.value) {
    const saved = sessionStorage.getItem('admin-news-edit')
    if (!saved) {
      showFailToast('编辑数据已失效，请重新选择新闻')
      router.replace('/admin/news')
      return
    }
    try {
      const item = JSON.parse(saved)
      if (String(item.id) !== String(route.params.id)) throw new Error('新闻 ID 不一致')
      fillForm(item)
    } catch {
      sessionStorage.removeItem('admin-news-edit')
      showFailToast('编辑数据无效，请重新选择新闻')
      router.replace('/admin/news')
    }
  } else if (store.currentCategoryId) {
    form.categoryId = store.currentCategoryId
  }
})
</script>

<style scoped>
.admin-form-page { min-height: 100vh; background: var(--background-color); }
.news-form { padding-top: 62px; padding-bottom: 28px; }
.submit-area { margin: 22px 16px; }
.native-field { display: flex; align-items: center; min-height: 48px; padding: 0 16px; background: #fff; }
.native-field label { width: 6.2em; color: #646566; }
.native-field select { flex: 1; min-width: 0; padding: 8px; border: 1px solid #dcdee0; border-radius: 5px; background: #fff; color: #323233; }
.image-preview { position: relative; margin: 8px 16px 14px 106px; min-height: 90px; }
.image-preview img { width: 140px; height: 90px; object-fit: cover; border-radius: 6px; background: #f2f3f5; }
.image-preview span { display: block; color: #ee0a24; font-size: 12px; margin-top: 4px; }
</style>
