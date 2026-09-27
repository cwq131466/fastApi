import { request } from '@/utils'

export default {
  // 分类接口
  getCategoryTree: () => request.get('/script/category/tree'),
  getCategoryList: (params = {}) => request.get('/script/category/list', { params }),
  createCategory: (data = {}) => request.post('/script/category/create', data),
  updateCategory: (data = {}) => request.post('/script/category/update', data),
  deleteCategory: (params = {}) => request.delete('/script/category/delete', { params }),

  // 脚本接口
  getScriptList: (params = {}) => request.get('/script/list', { params }),
  getScriptDetail: (params = {}) => request.get('/script/get', { params }),
  createScript: (data = {}) => request.post('/script/create', data),
  updateScript: (data = {}) => request.post('/script/update', data),
  deleteScript: (params = {}) => request.delete('/script/delete', { params }),

  // 文件上传接口
  uploadFile: (formData) => request.post('/script/upload/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteFile: (data) => request.post('/script/upload/delete', data),
  listFiles: (data) => request.post('/script/upload/list', data),
  getScriptFiles: (scriptId) => request.get('/script/upload/script-files', { params: { script_id: scriptId } }),
  
  // 角色接口（用于权限选择器）
  getRoleList: (params = {}) => request.get('/role/list', { params }),
}
