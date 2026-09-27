import { ElLoading } from 'element-plus'

let loadingInstance = null

export function showGlobalLoading(text = '加载中...', progress = 0) {
  if (loadingInstance) {
    return
  }
  
  loadingInstance = ElLoading.service({
    lock: true,
    text: text,
    background: 'rgba(255, 255, 255, 0.9)',
    customClass: 'global-loading'
  })
}

export function updateLoadingText(text) {
  if (loadingInstance) {
    loadingInstance.setText(text)
  }
}

export function closeGlobalLoading() {
  if (loadingInstance) {
    loadingInstance.close()
    loadingInstance = null
  }
}
