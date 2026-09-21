import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import axios from 'axios'

import { useAdminNewsStore } from '../store/modules/adminNews'
import { useUserStore } from '../store/user'


vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('admin news store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useUserStore().token = 'admin-token'
  })

  it('loads categories and a normalized paginated list', async () => {
    axios.get
      .mockResolvedValueOnce({ data: { data: [{ id: 3, name: '科技' }] } })
      .mockResolvedValueOnce({
        data: {
          data: {
            list: [{ id: 8, title: '新闻', category_id: 3, publish_time: '2026-01-01' }],
            total: 11,
            hasMore: true,
          },
        },
      })
    const store = useAdminNewsStore()

    expect((await store.fetchCategories()).success).toBe(true)
    expect(store.currentCategoryId).toBe(3)
    expect((await store.fetchNews(2)).success).toBe(true)
    expect(store.page).toBe(2)
    expect(store.newsList[0].categoryId).toBe(3)
    expect(store.newsList[0].publishTime).toBe('2026-01-01')
    expect(store.loading).toBe(false)
  })

  it('clears the list when no category is selected', async () => {
    const store = useAdminNewsStore()
    store.newsList = [{ id: 1 }]
    store.total = 1
    store.hasMore = true

    expect((await store.fetchNews()).success).toBe(true)
    expect(store.newsList).toEqual([])
    expect(store.total).toBe(0)
  })

  it('creates, partially updates, and deletes with bearer auth', async () => {
    axios.post.mockResolvedValueOnce({
      data: { data: { id: 1, category_id: 2, publish_time: '2026-02-01' } },
    })
    axios.patch.mockResolvedValueOnce({
      data: { data: { id: 1, title: '新标题', categoryId: 2 } },
    })
    axios.delete.mockResolvedValueOnce({ data: { code: 200 } })
    const store = useAdminNewsStore()

    const created = await store.createNews({ title: '标题' })
    expect(created.data.categoryId).toBe(2)
    expect((await store.updateNews(1, { title: '新标题' })).success).toBe(true)
    expect((await store.deleteNews(1)).success).toBe(true)
    expect(axios.patch).toHaveBeenCalledWith(
      expect.stringContaining('/api/admin/news/1'),
      { title: '新标题' },
      { headers: { Authorization: 'Bearer admin-token' } },
    )
  })

  it.each([
    ['fetchCategories', () => useAdminNewsStore().fetchCategories()],
    ['fetchNews', () => {
      const store = useAdminNewsStore()
      store.currentCategoryId = 1
      return store.fetchNews()
    }],
    ['createNews', () => useAdminNewsStore().createNews({})],
    ['updateNews', () => useAdminNewsStore().updateNews(1, {})],
    ['deleteNews', () => useAdminNewsStore().deleteNews(1)],
  ])('returns status and message when %s fails', async (_name, action) => {
    const failure = { response: { status: 403, data: { message: '无管理员权限' } } }
    axios.get.mockRejectedValueOnce(failure)
    axios.post.mockRejectedValueOnce(failure)
    axios.patch.mockRejectedValueOnce(failure)
    axios.delete.mockRejectedValueOnce(failure)

    expect(await action()).toMatchObject({
      success: false,
      status: 403,
      message: '无管理员权限',
    })
  })
})
