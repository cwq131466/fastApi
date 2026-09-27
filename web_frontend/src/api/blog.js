import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.token = token
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 直接返回完整响应数据
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
)

export default {
  // === 文章相关 ===
  getArticleList: (params = {}) => apiClient.get('/blog/article/list', { params }),
  getArticleById: (params = {}) => apiClient.get('/blog/article/get', { params }),
  getArticleRevisions: (params = {}) => apiClient.get('/blog/article/revisions', { params }),
  getRevisionDetail: (params = {}) => apiClient.get('/blog/article/revision/detail', { params }),
  getAuthorRanking: () => apiClient.get('/blog/article/author/ranking'),

  // === 统计相关 ===
  getMyArticleStats: () => apiClient.get('/blog/article/stats/my'),
  getSharedArticleStats: () => apiClient.get('/blog/article/stats/shared'),

  // === 分类相关 ===
  getCategoryTree: () => apiClient.get('/blog/category/tree'),
  getCategoryList: (params = {}) => apiClient.get('/blog/category/list', { params }),

  // === 标签相关 ===
  getTagList: (params = {}) => apiClient.get('/blog/tag/list', { params }),

  // === 点赞相关 ===
  toggleLike: (data = {}) => apiClient.post('/blog/article/like', data),
  getLikeStatus: (params = {}) => apiClient.get('/blog/article/like/status', { params }),

  // === 收藏相关 ===
  toggleFavorite: (data = {}) => apiClient.post('/blog/article/favorite', data),
  getFavoriteStatus: (params = {}) => apiClient.get('/blog/article/favorite/status', { params }),
  getFavoriteList: (params = {}) => apiClient.get('/blog/article/favorite/list', { params }),
}
