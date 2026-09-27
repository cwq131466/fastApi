import { apiClient } from './auth'

/**
 * 获取资产列表
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @param {string} [params.keyword] - 搜索关键词
 */
export function getAssets(params) {
  return apiClient.get('/assets/', { params })
}

/**
 * 获取资产详情
 * @param {string} assetId - 资产ID
 */
export function getAssetDetail(assetId) {
  return apiClient.get(`/assets/${assetId}`)
}

/**
 * 获取交换机端口状态（普通方式）
 * @param {string} assetId - 资产ID
 */
export function getSwitchPorts(assetId) {
  return apiClient.get(`/assets/${assetId}/ports`)
}

/**
 * 获取交换机端口状态（流式方式，带实时进度）
 * @param {string} assetId - 资产ID
 * @param {Object} callbacks - 回调函数
 * @param {Function} callbacks.onProgress - 进度回调 (phase, message)
 * @param {Function} callbacks.onComplete - 完成回调 (data)
 * @param {Function} callbacks.onError - 错误回调 (error)
 * @returns {EventSource} 返回 EventSource 实例，可用于手动关闭
 */
export function getSwitchPortsStream(assetId, callbacks = {}) {
  const { onProgress, onComplete, onError } = callbacks
  
  // 获取 token
  const token = localStorage.getItem('token') || localStorage.getItem('access_token')
  
  // 构建 SSE URL，通过查询参数传递 token
  const url = `/api/v1/assets/${assetId}/ports/stream?token=${encodeURIComponent(token || '')}`
  
  // 创建 EventSource（注意：EventSource 不支持自定义 headers）
  const eventSource = new EventSource(url)
  
  // 监听进度事件
  eventSource.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('[SSE Progress]', data.phase, data.message)
      if (onProgress) {
        onProgress(data.phase, data.message)
      }
    } catch (e) {
      console.error('[SSE Parse Error]', e)
    }
  })
  
  // 监听完成事件
  eventSource.addEventListener('complete', (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('[SSE Complete]', data)
      eventSource.close()
      if (onComplete) {
        onComplete(data)
      }
    } catch (e) {
      console.error('[SSE Parse Error]', e)
    }
  })
  
  // 监听错误事件
  eventSource.addEventListener('error', (event) => {
    try {
      const data = JSON.parse(event.data)
      console.error('[SSE Error]', data)
      eventSource.close()
      if (onError) {
        onError(data)
      }
    } catch (e) {
      console.error('[SSE Error Parse]', e)
    }
  })
  
  // 监听连接错误
  eventSource.onerror = (error) => {
    console.error('[SSE Connection Error]', error)
    eventSource.close()
    if (onError) {
      onError({ error: '连接失败' })
    }
  }
  
  return eventSource
}

/**
 * 健康检查
 */
export function healthCheck() {
  return apiClient.get('/assets/health')
}

/**
 * 切换端口 dot1x 认证状态
 * @param {string} switchIp - 交换机 IP 地址
 * @param {string} portName - 端口名称
 * @param {Object} data - 请求数据
 * @param {boolean} data.enable - True 为开启，False 为关闭
 * @param {string} data.jumpserver_username - JumpServer 用户名
 * @param {string} data.jumpserver_password - JumpServer 密码
 */
export function togglePortDot1x(switchIp, portName, data) {
  return apiClient.post('/assets/ports/dot1x', {
    switch_ip: switchIp,
    port_name: portName,
    ...data
  })
}

export default {
  getAssets,
  getAssetDetail,
  getSwitchPorts,
  getSwitchPortsStream,
  healthCheck,
  togglePortDot1x
}