import { showFailToast } from 'vant'

import pinia from '../store'
import { useUserStore } from '../store/user'


export const routeGuard = async (to, _from, next) => {
  document.title = to.meta.title || '新闻资讯'

  if (to.meta.requiresAuth) {
    const userStore = useUserStore(pinia)
    if (!userStore.getLoginStatus || !userStore.token) {
      showFailToast('请先登录')
      next('/login')
      return
    }
  }

  if (to.meta.requiresAdmin) {
    const userStore = useUserStore(pinia)
    if (!userStore.getLoginStatus || !userStore.token) {
      showFailToast('请先登录管理员账户')
      next('/login')
      return
    }

    // 兼容升级前持久化在浏览器中的旧用户信息。
    if (!userStore.userInfo || typeof userStore.userInfo.isAdmin === 'undefined') {
      await userStore.getUserInfoDetail()
    }

    if (!userStore.getIsAdmin) {
      showFailToast('无管理员权限')
      next('/my')
      return
    }
  }

  next()
}
