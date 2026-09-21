import { defineStore } from 'pinia'
import axios from 'axios'

import { apiConfig } from '../../config/api'
import { useUserStore } from '../user'


const normalizeNews = (item) => ({
  ...item,
  categoryId: item.categoryId ?? item.category_id,
  publishTime: item.publishTime ?? item.publish_time,
})

const requestError = (error, fallback) => ({
  success: false,
  status: error.response?.status,
  message: error.response?.data?.message || fallback,
})

export const useAdminNewsStore = defineStore('adminNews', {
  state: () => ({
    categories: [],
    newsList: [],
    currentCategoryId: null,
    page: 1,
    pageSize: 10,
    total: 0,
    hasMore: false,
    loading: false,
  }),

  actions: {
    adminHeaders() {
      const userStore = useUserStore()
      return { Authorization: `Bearer ${userStore.token}` }
    },

    async fetchCategories() {
      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/news/categories`)
        this.categories = response.data?.data || []
        if (!this.currentCategoryId && this.categories.length) {
          this.currentCategoryId = this.categories[0].id
        }
        return { success: true }
      } catch (error) {
        return requestError(error, '获取新闻分类失败')
      }
    },

    async fetchNews(page = this.page) {
      if (!this.currentCategoryId) {
        this.newsList = []
        this.total = 0
        this.hasMore = false
        return { success: true }
      }

      this.loading = true
      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/news/list`, {
          params: {
            categoryId: this.currentCategoryId,
            page,
            pageSize: this.pageSize,
          },
        })
        const data = response.data?.data || {}
        this.page = page
        this.newsList = (data.list || []).map(normalizeNews)
        this.total = data.total || 0
        this.hasMore = Boolean(data.hasMore)
        return { success: true }
      } catch (error) {
        return requestError(error, '获取新闻列表失败')
      } finally {
        this.loading = false
      }
    },

    async createNews(payload) {
      try {
        const response = await axios.post(
          `${apiConfig.baseURL}/api/admin/news`,
          payload,
          { headers: this.adminHeaders() },
        )
        return { success: true, data: normalizeNews(response.data?.data || {}) }
      } catch (error) {
        return requestError(error, '新增新闻失败')
      }
    },

    async updateNews(newsId, payload) {
      try {
        const response = await axios.patch(
          `${apiConfig.baseURL}/api/admin/news/${newsId}`,
          payload,
          { headers: this.adminHeaders() },
        )
        return { success: true, data: normalizeNews(response.data?.data || {}) }
      } catch (error) {
        return requestError(error, '修改新闻失败')
      }
    },

    async deleteNews(newsId) {
      try {
        await axios.delete(`${apiConfig.baseURL}/api/admin/news/${newsId}`, {
          headers: this.adminHeaders(),
        })
        return { success: true }
      } catch (error) {
        return requestError(error, '删除新闻失败')
      }
    },
  },
})
