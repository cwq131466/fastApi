import { request } from '@/utils'

export default {
  // === 文章管理 ===
  getArticleList: (params = {}) => request.get('/blog/article/list', { params }),
  getArticleById: (params = {}) => request.get('/blog/article/get', { params }),
  createArticle: (data = {}) => request.post('/blog/article/create', data),
  updateArticle: (data = {}) => request.post('/blog/article/update', data),
  deleteArticle: (params = {}) => request.delete('/blog/article/delete', { params }),
  restoreArticle: (data = {}) => request.post('/blog/article/restore', data),
  publishArticle: (data = {}) => request.post('/blog/article/publish', data),

  // === 分类管理 ===
  getCategoryTree: () => request.get('/blog/category/tree'),
  getCategoryList: (params = {}) => request.get('/blog/category/list', { params }),
  createCategory: (data = {}) => request.post('/blog/category/create', data),
  updateCategory: (data = {}) => request.post('/blog/category/update', data),
  deleteCategory: (params = {}) => request.delete('/blog/category/delete', { params }),

  // === 标签管理 ===
  getTagList: (params = {}) => request.get('/blog/tag/list', { params }),
  createTag: (data = {}) => request.post('/blog/tag/create', data),
  updateTag: (data = {}) => request.post('/blog/tag/update', data),
  deleteTag: (params = {}) => request.delete('/blog/tag/delete', { params }),

  // === 图片上传 ===
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post('/blog/upload/image', formData, {
      // 确保 axios 不转换 FormData
      transformRequest: [(data) => data],
    })
  },
  deleteImage: (params = {}) => request.delete('/blog/upload/image', { params }),

  // === 修订历史 ===
  getArticleRevisions: (params = {}) => request.get('/blog/article/revisions', { params }),
  rollbackToRevision: (data = {}) => request.post('/blog/article/revision/rollback', data),
}
