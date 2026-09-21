import { createRouter, createWebHistory } from 'vue-router'

import { routeGuard } from './guard'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: {
      title: '登录',
      keepAlive: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: {
      title: '注册',
      keepAlive: false
    }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: {
      title: '首页',
      keepAlive: true
    }
  },
  {
    path: '/news/detail/:id',
    name: 'NewsDetail',
    component: () => import('../views/NewsDetail.vue'),
    meta: {
      title: '新闻详情',
      keepAlive: false
    }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'),
    meta: {
      title: '浏览历史',
      keepAlive: false
    }
  },
  {
    path: '/favorite',
    name: 'Favorite',
    component: () => import('../views/Favorite.vue'),
    meta: {
      title: '我的收藏',
      keepAlive: false
    }
  },
  {
    path: '/category',
    name: 'Category',
    component: () => import('../views/Category.vue'),
    meta: {
      title: '分类',
      keepAlive: true
    }
  },
  {
    path: '/my',
    name: 'My',
    component: () => import('../views/My.vue'),
    meta: {
      title: '我的',
      keepAlive: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: {
      title: '个人信息',
      keepAlive: false
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: {
      title: '设置',
      keepAlive: false
    }
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('../views/Notifications.vue'),
    meta: {
      title: '消息通知',
      keepAlive: false,
      requiresAuth: true
    }
  },
  {
    path: '/admin/news',
    name: 'AdminNews',
    component: () => import('../views/AdminNews.vue'),
    meta: {
      title: '新闻管理',
      keepAlive: false,
      requiresAdmin: true
    }
  },
  {
    path: '/admin/news/create',
    name: 'AdminNewsCreate',
    component: () => import('../views/AdminNewsForm.vue'),
    meta: {
      title: '新增新闻',
      keepAlive: false,
      requiresAdmin: true
    }
  },
  {
    path: '/admin/news/:id/edit',
    name: 'AdminNewsEdit',
    component: () => import('../views/AdminNewsForm.vue'),
    meta: {
      title: '编辑新闻',
      keepAlive: false,
      requiresAdmin: true
    }
  },
  {
    path: '/admin/announcements/create',
    name: 'AnnouncementCreate',
    component: () => import('../views/AnnouncementForm.vue'),
    meta: {
      title: '发布公告',
      keepAlive: false,
      requiresAdmin: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/home'
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 全局前置守卫
router.beforeEach(routeGuard)

export default router
