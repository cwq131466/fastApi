import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import MainLayout from '../layout/MainLayout.vue'
import OAuthCallback from '../views/auth/OAuthCallback.vue'

// 懒加载页面组件
const Home = () => import('../views/Home.vue')
const Script = () => import('../views/Script.vue')
const ScriptLogs = () => import('../views/ScriptLogs.vue')
const Switch = () => import('../views/Switch.vue')
const Profile = () => import('../views/Profile.vue')

// Blog 模块
const BlogHome = () => import('../views/blog/index.vue')
const BlogDetail = () => import('../views/blog/detail.vue')
const BlogCategory = () => import('../views/blog/category.vue')
const BlogTag = () => import('../views/blog/tag.vue')
const MyArticles = () => import('../views/blog/my-articles.vue')
const AuthorArticles = () => import('../views/blog/author-articles.vue')

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/auth/callback',
    name: 'OAuthCallback',
    component: OAuthCallback
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: Home
      },
      {
        path: 'script',
        name: 'Script',
        component: Script
      },
      {
        path: 'scriptlogs',
        name: 'ScriptLogs',
        component: ScriptLogs
      },
      {
        path: 'switch',
        name: 'Switch',
        component: Switch,
        meta: { requiresAuth: true }
      },
      // Blog 模块路由（运维文档）
      {
        path: 'docs',
        name: 'Docs',
        component: BlogHome,
        meta: { requiresAuth: true }
      },
      {
        path: 'docs/detail/:id',
        name: 'BlogDetail',
        component: BlogDetail,
        meta: { requiresAuth: true }
      },
      {
        path: 'docs/category/:id',
        name: 'BlogCategory',
        component: BlogCategory,
        meta: { requiresAuth: true }
      },
      {
        path: 'docs/tag/:id',
        name: 'BlogTag',
        component: BlogTag,
        meta: { requiresAuth: true }
      },
      {
        path: 'docs/my-articles',
        name: 'MyArticles',
        component: MyArticles,
        meta: { requiresAuth: true }
      },
      {
        path: 'docs/author/:id',
        name: 'AuthorArticles',
        component: AuthorArticles,
        meta: { requiresAuth: true }
      },
      // 个人信息页面
      {
        path: 'profile',
        name: 'Profile',
        component: Profile,
        meta: { requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  // createWebHistory() 告诉 Vue Router 使用 HTML5 History API 来管理路由，这会生成干净的 URL（没有 # 符号）。
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 白名单路径（不需要认证）
  const whiteList = ['/login', '/auth/callback']
  
  if (whiteList.includes(to.path)) {
    // 如果已登录且访问登录页，跳转到首页
    if (to.path === '/login' && token) {
      next('/home')
    } else {
      next()
    }
  } else if (to.meta.requiresAuth && !token) {
    // 需要认证但没有token，跳转到登录页
    next('/login')
  } else {
    next()
  }
})

export default router