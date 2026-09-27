import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.token = token
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 获取分类树
export const getCategoryTree = () => {
  return apiClient.get('/script/category/tree')
}

// 获取脚本列表
export const getScriptList = (params = {}) => {
  return apiClient.get('/script/list', { params })
}

// 获取脚本执行日志列表
export const getScriptLogList = (params = {}) => {
  return apiClient.get('/scriptlog/list', { params })
}

export default {
  getCategoryTree,
  getScriptList,
  getScriptLogList
}
