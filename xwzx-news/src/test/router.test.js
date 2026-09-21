import { beforeEach, describe, expect, it, vi } from 'vitest'


const { showFailToast } = vi.hoisted(() => ({ showFailToast: vi.fn() }))
vi.mock('vant', () => ({ showFailToast }))

import pinia from '../store'
import { useUserStore } from '../store/user'
import { routeGuard } from '../router/guard'


describe('admin route guard', () => {
  beforeEach(() => {
    const store = useUserStore(pinia)
    store.$reset()
    showFailToast.mockClear()
  })

  it('protects ordinary authenticated routes', async () => {
    const next = vi.fn()
    await routeGuard({ meta: { title: '消息通知', requiresAuth: true } }, {}, next)

    expect(document.title).toBe('消息通知')
    expect(showFailToast).toHaveBeenCalledWith('请先登录')
    expect(next).toHaveBeenCalledWith('/login')
  })

  it('redirects guests to login', async () => {
    const next = vi.fn()
    await routeGuard({ meta: { title: '新闻管理', requiresAdmin: true } }, {}, next)

    expect(document.title).toBe('新闻管理')
    expect(showFailToast).toHaveBeenCalledWith('请先登录管理员账户')
    expect(next).toHaveBeenCalledWith('/login')
  })

  it('refreshes legacy user data and rejects a non-admin', async () => {
    const store = useUserStore(pinia)
    store.token = 'reader-token'
    store.isLogin = true
    store.userInfo = { username: 'reader' }
    store.getUserInfoDetail = vi.fn(async () => {
      store.userInfo = { username: 'reader', isAdmin: false }
      return { success: true }
    })
    const next = vi.fn()

    await routeGuard({ meta: { requiresAdmin: true } }, {}, next)
    expect(store.getUserInfoDetail).toHaveBeenCalled()
    expect(showFailToast).toHaveBeenCalledWith('无管理员权限')
    expect(next).toHaveBeenCalledWith('/my')
  })

  it('allows admins and ordinary public routes', async () => {
    const store = useUserStore(pinia)
    store.token = 'admin-token'
    store.isLogin = true
    store.userInfo = { username: 'admin', isAdmin: true }
    const adminNext = vi.fn()
    await routeGuard({ meta: { requiresAdmin: true } }, {}, adminNext)
    expect(adminNext).toHaveBeenCalledWith()

    const publicNext = vi.fn()
    await routeGuard({ meta: {} }, {}, publicNext)
    expect(document.title).toBe('新闻资讯')
    expect(publicNext).toHaveBeenCalledWith()
  })
})
