<template>
  <div class="admin-news-page">
    <van-nav-bar
      title="新闻管理"
      left-text="返回"
      left-arrow
      right-text="新增"
      fixed
      @click-left="router.push('/my')"
      @click-right="router.push('/admin/news/create')"
    />

    <div class="page-content">
      <div class="category-card">
        <label for="admin-category">新闻分类</label>
        <select id="admin-category" v-model.number="selectedCategory" @change="changeCategory">
          <option v-for="category in store.categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
      </div>

      <van-empty v-if="!store.loading && !store.newsList.length" description="当前分类暂无新闻" />

      <div v-else class="news-list">
        <article v-for="item in store.newsList" :key="item.id" class="news-card">
          <img v-if="item.image" :src="item.image" :alt="item.title" class="cover" />
          <div v-else class="cover cover-placeholder">暂无图片</div>
          <div class="news-main">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description || '暂无简介' }}</p>
            <div class="meta">
              <span>{{ item.author || '未知作者' }}</span>
              <span>ID: {{ item.id }}</span>
            </div>
            <div class="actions">
              <van-button size="small" type="primary" plain @click="editNews(item)">编辑</van-button>
              <van-button size="small" type="danger" plain @click="confirmDelete(item)">删除</van-button>
            </div>
          </div>
        </article>
      </div>

      <div class="pagination" v-if="store.total > 0">
        <van-button size="small" :disabled="store.page <= 1 || store.loading" @click="previousPage">
          上一页
        </van-button>
        <span>第 {{ store.page }} 页 · 共 {{ store.total }} 条</span>
        <van-button size="small" :disabled="!store.hasMore || store.loading" @click="nextPage">
          下一页
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showFailToast, showSuccessToast } from 'vant'

import { useAdminNewsStore } from '../store/modules/adminNews'

const router = useRouter()
const store = useAdminNewsStore()
const selectedCategory = ref(null)

const showError = (result) => {
  if (result.status === 401 || result.status === 403) {
    showFailToast('无管理员权限')
    router.replace('/my')
    return
  }
  showFailToast(result.message || '操作失败')
}

const loadNews = async (page = 1) => {
  const result = await store.fetchNews(page)
  if (!result.success) showError(result)
}

const changeCategory = async () => {
  store.currentCategoryId = selectedCategory.value
  await loadNews(1)
}

const previousPage = () => loadNews(store.page - 1)
const nextPage = () => loadNews(store.page + 1)

const editNews = (item) => {
  sessionStorage.setItem('admin-news-edit', JSON.stringify(item))
  router.push(`/admin/news/${item.id}/edit`)
}

const confirmDelete = async (item) => {
  try {
    await showConfirmDialog({
      title: '确定删除？',
      message: `删除“${item.title}”后，相关收藏和浏览历史也会被删除。`,
      confirmButtonText: '确定删除',
      confirmButtonColor: '#ee0a24',
    })
  } catch {
    return
  }

  const result = await store.deleteNews(item.id)
  if (!result.success) {
    showError(result)
    return
  }

  showSuccessToast('删除新闻成功')
  const targetPage = store.newsList.length === 1 && store.page > 1 ? store.page - 1 : store.page
  await loadNews(targetPage)
}

onMounted(async () => {
  const result = await store.fetchCategories()
  if (!result.success) {
    showError(result)
    return
  }
  selectedCategory.value = store.currentCategoryId
  await loadNews(1)
})
</script>

<style scoped>
.admin-news-page { min-height: 100vh; background: var(--background-color); }
.page-content { padding: 62px 12px 28px; }
.category-card { background: #fff; padding: 14px; border-radius: 10px; margin-bottom: 12px; }
.category-card label { display: block; color: #666; margin-bottom: 8px; }
.category-card select { width: 100%; padding: 10px; border: 1px solid #dcdee0; border-radius: 6px; background: #fff; color: #333; }
.news-card { display: flex; gap: 12px; padding: 12px; margin-bottom: 10px; background: #fff; border-radius: 10px; }
.cover { width: 96px; height: 78px; flex: 0 0 96px; object-fit: cover; border-radius: 6px; }
.cover-placeholder { display: flex; align-items: center; justify-content: center; background: #f2f3f5; color: #969799; font-size: 12px; }
.news-main { min-width: 0; flex: 1; }
.news-main h3 { font-size: 15px; line-height: 1.4; margin-bottom: 5px; }
.news-main p { color: #666; font-size: 13px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.meta { display: flex; gap: 12px; margin-top: 7px; color: #969799; font-size: 12px; }
.actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 10px; }
.pagination { display: flex; align-items: center; justify-content: space-between; padding: 14px 4px 0; color: #666; font-size: 13px; }
</style>
