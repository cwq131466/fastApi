import i18n from '~/i18n'
const { t } = i18n.global

const Layout = () => import('@/layout/index.vue')

export const basicRoutes = [
  {
    path: '/',
    redirect: '/workbench', // 默认跳转到首页
    meta: { order: 0 },
  },
  {
    name: t('views.workbench.label_workbench'),
    path: '/workbench',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/workbench/index.vue'),
        name: `${t('views.workbench.label_workbench')}Default`,
        meta: {
          title: t('views.workbench.label_workbench'),
          icon: 'icon-park-outline:workbench',
          affix: true,
        },
      },
    ],
    meta: { order: 1 },
  },
  {
    name: t('views.profile.label_profile'),
    path: '/profile',
    component: Layout,
    isHidden: true,
    children: [
      {
        path: '',
        component: () => import('@/views/profile/index.vue'),
        name: `${t('views.profile.label_profile')}Default`,
        meta: {
          title: t('views.profile.label_profile'),
          icon: 'user',
          affix: true,
        },
      },
    ],
    meta: { order: 99 },
  },
  {
    name: 'Tools',
    path: '/tools',
    component: Layout,
    redirect: '/tools/script',
    meta: {
      title: '工具中心',
      icon: 'mdi:tools',
      order: 5,
    },
    children: [
      {
        name: 'ScriptManage',
        path: 'script',
        component: () => import('@/views/tools/script/index.vue'),
        meta: {
          title: '运维脚本',
          icon: 'mdi:code-braces',
        },
      },
    ],
  },
  {
    name: 'BlogManage',
    path: '/blog',
    component: Layout,
    redirect: '/blog/article',
    meta: {
      title: '文档管理',
      icon: 'mdi:file-document-multiple',
      order: 6,
    },
    children: [
      {
        name: 'ArticleManage',
        path: 'article',
        component: () => import('@/views/blog/article/index.vue'),
        meta: {
          title: '文章管理',
          icon: 'mdi:newspaper-variant',
        },
      },
      {
        name: 'CategoryManage',
        path: 'category',
        component: () => import('@/views/blog/category/index.vue'),
        meta: {
          title: '分类管理',
          icon: 'mdi:folder-tree',
        },
      },
      {
        name: 'TagManage',
        path: 'tag',
        component: () => import('@/views/blog/tag/index.vue'),
        meta: {
          title: '标签管理',
          icon: 'mdi:tag-multiple',
        },
      },
    ],
  },
  // 文章编辑器（隐藏路由）
  {
    name: 'ArticleEditor',
    path: '/blog/article/editor',
    component: Layout,
    isHidden: true,
    children: [
      {
        path: '',
        component: () => import('@/views/blog/article/editor.vue'),
        name: 'ArticleEditorDefault',
        meta: {
          title: '编辑文章',
        },
      },
    ],
  },
  {
    name: 'ErrorPage',
    path: '/error-page',
    component: Layout,
    redirect: '/error-page/404',
    meta: {
      title: t('views.errors.label_error'),
      icon: 'mdi:alert-circle-outline',
      order: 99,
    },
    children: [
      {
        name: 'ERROR-401',
        path: '401',
        component: () => import('@/views/error-page/401.vue'),
        meta: {
          title: '401',
          icon: 'material-symbols:authenticator',
        },
      },
      {
        name: 'ERROR-403',
        path: '403',
        component: () => import('@/views/error-page/403.vue'),
        meta: {
          title: '403',
          icon: 'solar:forbidden-circle-line-duotone',
        },
      },
      {
        name: 'ERROR-404',
        path: '404',
        component: () => import('@/views/error-page/404.vue'),
        meta: {
          title: '404',
          icon: 'tabler:error-404',
        },
      },
      {
        name: 'ERROR-500',
        path: '500',
        component: () => import('@/views/error-page/500.vue'),
        meta: {
          title: '500',
          icon: 'clarity:rack-server-outline-alerted',
        },
      },
    ],
  },
  {
    name: '403',
    path: '/403',
    component: () => import('@/views/error-page/403.vue'),
    isHidden: true,
  },
  {
    name: '404',
    path: '/404',
    component: () => import('@/views/error-page/404.vue'),
    isHidden: true,
  },
  {
    name: 'Login',
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    isHidden: true,
    meta: {
      title: '登录页',
    },
  },
  {
    name: 'OAuthCallback',
    path: '/auth/callback',
    component: () => import('@/views/auth/OAuthCallback.vue'),
    isHidden: true,
    meta: {
      title: 'OAuth回调',
    },
  },
]

export const NOT_FOUND_ROUTE = {
  name: 'NotFound',
  path: '/:pathMatch(.*)*',
  redirect: '/404',
  isHidden: true,
}

export const EMPTY_ROUTE = {
  name: 'Empty',
  path: '/:pathMatch(.*)*',
  component: null,
}

const modules = import.meta.glob('@/views/**/route.js', { eager: true })
const asyncRoutes = []
Object.keys(modules).forEach((key) => {
  asyncRoutes.push(modules[key].default)
})

// 加载 views 下每个模块的 index.vue 文件
const vueModules = import.meta.glob('@/views/**/index.vue')

export { asyncRoutes, vueModules }
