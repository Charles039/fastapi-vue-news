import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import axios from 'axios'

import { useUserStore } from '../store/user'


vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

const successfulAuth = {
  data: {
    code: 200,
    data: {
      token: 'admin-token',
      userInfo: { id: 1, username: 'admin', isAdmin: true, bio: '简介' },
    },
  },
}

describe('user store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('logs in, exposes admin status, and logs out', async () => {
    axios.post.mockResolvedValueOnce(successfulAuth)
    const store = useUserStore()
    const result = await store.login({ username: 'admin', password: 'pass123' })

    expect(result.success).toBe(true)
    expect(store.getLoginStatus).toBe(true)
    expect(store.getIsAdmin).toBe(true)
    expect(store.getUserBio).toBe('简介')
    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/user/login'),
      { username: 'admin', password: 'pass123' },
    )

    store.logout()
    expect(store.token).toBe('')
    expect(store.getIsAdmin).toBe(false)
    expect(store.getUserBio).toBe('这是我的个人简介')
  })

  it('registers and handles unsuccessful auth responses', async () => {
    axios.post
      .mockResolvedValueOnce(successfulAuth)
      .mockResolvedValueOnce({ data: { code: 400, message: '用户已存在' } })
      .mockRejectedValueOnce({ response: { data: { message: '登录失败' } } })

    const store = useUserStore()
    expect((await store.register({ username: 'new', password: 'pass123' })).success).toBe(true)
    expect((await store.register({ username: 'new', password: 'pass123' }))).toEqual({
      success: false,
      message: '用户已存在',
    })
    expect((await store.login({ username: 'new', password: 'bad' }))).toEqual({
      success: false,
      message: '登录失败',
    })
  })

  it('refreshes user information and updates profile/password', async () => {
    const store = useUserStore()
    expect((await store.getUserInfoDetail()).message).toBe('未登录')
    expect((await store.updateUserBio('内容')).message).toBe('未登录')
    expect((await store.updatePassword('old', 'newpass')).message).toBe('未登录')

    store.token = 'token'
    store.userInfo = { bio: '旧简介', isAdmin: false }
    axios.get.mockResolvedValueOnce({
      data: { code: 200, data: { username: 'reader', bio: '服务端简介', isAdmin: false } },
    })
    axios.put
      .mockResolvedValueOnce({ data: { code: 200 } })
      .mockResolvedValueOnce({ data: { code: 200 } })

    const info = await store.getUserInfoDetail()
    expect(info.success).toBe(true)
    expect(store.userInfo.bio).toBe('服务端简介')
    expect((await store.updateUserBio('新简介')).success).toBe(true)
    expect(store.userInfo.bio).toBe('新简介')
    expect((await store.updatePassword('old', 'newpass')).success).toBe(true)
  })

  it('returns API errors from profile actions', async () => {
    const store = useUserStore()
    store.token = 'token'
    store.userInfo = { bio: '' }
    const failure = { response: { data: { message: '服务错误' } } }
    axios.get.mockRejectedValueOnce(failure)
    axios.put.mockRejectedValueOnce(failure).mockRejectedValueOnce(failure)

    expect((await store.getUserInfoDetail()).message).toBe('服务错误')
    expect((await store.updateUserBio('x')).message).toBe('服务错误')
    expect((await store.updatePassword('a', 'bbbbbb')).message).toBe('服务错误')
  })
})
