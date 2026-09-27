import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 增加到60秒，以适应SSH连接交换机的耗时操作
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

// 响应拦截器 - 直接返回完整响应数据
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
)

export const login = (username, password) => {
  return apiClient.post('/base/access_token', {
    username,
    password
  })
}

export const getUserInfo = () => {
  return apiClient.get('/base/userinfo')
}

export const updatePassword = (data) => {
  return apiClient.post('/base/update_password', data)
}

// OAuth2 登出接口
// 注意：不需要传递参数，后端会从请求头中的 JWT token 获取用户信息
export const oauthLogout = () => {
  return apiClient.post('/auth/logout')
}

// 上传头像接口
export const uploadAvatar = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  // 创建单独的 axios 实例用于文件上传（需要 multipart/form-data）
  const fileClient = axios.create({
    baseURL: '/api/v1',
    timeout: 60000,
    headers: {} // 不设置 Content-Type，让浏览器自动设置
  })
  
  // 添加响应拦截器，与其他 API 保持一致
  fileClient.interceptors.response.use(
    (response) => response.data,
    (error) => Promise.reject(error)
  )
  
  // 添加 token
  const token = localStorage.getItem('token')
  if (token) {
    fileClient.defaults.headers.token = token
  }
  
  return fileClient.post('/user/avatar', formData)
}

export { apiClient }

export default {
  login,
  getUserInfo,
  updatePassword,
  oauthLogout,
  uploadAvatar
}
