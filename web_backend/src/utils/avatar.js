/**
 * 根据用户名生成颜色索引（确定性）
 * @param {string} name - 用户名
 * @returns {number} 颜色索引
 */
function getColorIndex(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash)
}

/**
 * 预定义的 GitHub 风格颜色 palette
 */
const COLORS = [
  '#FF6B6B', // 红色
  '#FF922B', // 橙色
  '#FCC419', // 黄色
  '#51CF66', // 绿色
  '#339AF0', // 蓝色
  '#845EF7', // 紫色
  '#F06595', // 粉色
  '#20C997', // 青色
  '#FFA94D', // 浅橙
  '#74C0FC', // 浅蓝
  '#B197FC', // 浅紫
  '#69DB7C', // 浅绿
]

/**
 * 获取用户名对应的背景色
 * @param {string} name - 用户名
 * @returns {string} 十六进制颜色值
 */
function getBackgroundColor(name) {
  const index = getColorIndex(name) % COLORS.length
  return COLORS[index]
}

/**
 * 使用 Canvas 生成基于用户名的默认头像（Base64）
 * @param {string} name - 用户名或姓名
 * @param {number} size - 头像尺寸（默认 200）
 * @returns {string} Base64 编码的图片 URL
 */
export function generateInitialAvatar(name, size = 200) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  
  canvas.width = size
  canvas.height = size
  
  // 获取首字母
  const initials = name ? name.charAt(0).toUpperCase() : '?'
  
  // 绘制背景
  const bgColor = getBackgroundColor(name || '?')
  ctx.fillStyle = bgColor
  ctx.fillRect(0, 0, size, size)
  
  // 绘制文字
  ctx.fillStyle = '#FFFFFF'
  ctx.font = `bold ${size * 0.5}px Arial, sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(initials, size / 2, size / 2)
  
  // 转换为 Base64
  return canvas.toDataURL('image/png')
}

/**
 * 获取头像 URL - 如果有自定义头像则返回，否则生成本地默认头像
 * @param {string|null} avatarUrl - 后端返回的自定义头像 URL
 * @param {string} username - 用户名（用于生成默认头像）
 * @returns {string} 最终头像 URL（自定义 URL 或 Base64）
 */
export function getAvatarUrl(avatarUrl, username = '') {
  if (avatarUrl && avatarUrl.trim()) {
    return avatarUrl
  }
  return generateInitialAvatar(username || '?')
}

/**
 * 获取图片完整URL - 处理后端返回的相对路径
 * @param {string|null} path - 图片路径（可能是相对路径或绝对路径）
 * @returns {string} 处理后的图片URL
 */
export function getImageUrl(path) {
  if (!path) return ''
  // 如果已经是完整URL，直接返回
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  // 如果以/uploads开头，直接返回（开发环境会通过代理，生产环境通过Nginx）
  if (path.startsWith('/uploads')) return path
  // 其他情况添加/uploads前缀
  return `/uploads/${path}`
}
