import MarkdownIt from 'markdown-it'

// 初始化 Markdown 解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
})

// HTML 转义
function escapeHtml(text) {
  if (!text) return ''
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * LCS (Longest Common Subsequence) 算法
 * 找出两个数组的最长公共子序列，用于智能 diff
 */
function lcs(oldArr, newArr) {
  const m = oldArr.length
  const n = newArr.length
  
  // 创建 DP 表
  const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0))

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldArr[i - 1] === newArr[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  // 回溯找出差异
  let i = m, j = n
  const result = []

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldArr[i - 1] === newArr[j - 1]) {
      // 相同的行
      result.unshift({ type: 'unchanged', value: oldArr[i - 1] })
      i--
      j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      // 新增的行（在新文本中但不在旧文本中）
      result.unshift({ type: 'added', value: newArr[j - 1] })
      j--
    } else {
      // 删除的行（在旧文本中但不在新文本中）
      result.unshift({ type: 'removed', value: oldArr[i - 1] })
      i--
    }
  }

  return result
}

/**
 * 字符级差异对比（用于行内变化）
 */
export function computeCharDiff(oldStr, newStr) {
  if (oldStr === newStr) return null

  const m = oldStr.length
  const n = newStr.length

  // 创建 DP 表
  const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0))

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldStr[i - 1] === newStr[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  // 回溯找出差异
  let i = m, j = n
  const deleted = []
  const added = []

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldStr[i - 1] === newStr[j - 1]) {
      i--
      j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      added.unshift(newStr[j - 1])
      j--
    } else {
      deleted.unshift(oldStr[i - 1])
      i--
    }
  }

  return {
    deleted: deleted.join(''),
    added: added.join('')
  }
}

/**
 * 高级 Markdown 差异对比
 * 使用 LCS 算法进行智能行级对比
 */
export function generateMarkdownDiff(oldText, newText) {
  if (!oldText && !newText) return '<div class="diff-empty">无内容</div>'

  if (!oldText) {
    const rendered = md.render(newText)
    return `<div class="diff-block diff-added">${rendered}</div>`
  }

  if (!newText) {
    const rendered = md.render(oldText)
    return `<div class="diff-block diff-removed">${rendered}</div>`
  }

  if (oldText === newText) {
    const rendered = md.render(oldText)
    return `<div class="diff-block diff-unchanged">${rendered}</div>`
  }

  // 按行分割
  const oldLines = oldText.split('\n')
  const newLines = newText.split('\n')

  console.log('旧文本行数:', oldLines.length)
  console.log('新文本行数:', newLines.length)

  // 使用 LCS 算法找出差异
  const diff = lcs(oldLines, newLines)

  // 生成 HTML
  const result = []

  diff.forEach((item, index) => {
    const line = item.value

    if (item.type === 'unchanged') {
      // 相同的行
      if (line.trim() === '') {
        result.push('<div class="diff-line diff-unchanged">&nbsp;</div>')
      } else {
        const rendered = md.renderInline(line)
        result.push(`<div class="diff-line diff-unchanged">${rendered}</div>`)
      }
    } else if (item.type === 'added') {
      // 新增的行
      if (line.trim() === '') {
        result.push('<div class="diff-line diff-added">&nbsp;</div>')
      } else {
        // 检查是否是 Markdown 语法
        if (line.startsWith('#') || line.startsWith('- ') || line.startsWith('* ') || line.startsWith('> ') || line.startsWith('```')) {
          const rendered = md.render(line)
          result.push(`<div class="diff-line diff-added rendered">${rendered}</div>`)
        } else {
          result.push(`<div class="diff-line diff-added">+ ${escapeHtml(line)}</div>`)
        }
      }
    } else if (item.type === 'removed') {
      // 删除的行
      if (line.trim() === '') {
        result.push('<div class="diff-line diff-removed">&nbsp;</div>')
      } else {
        if (line.startsWith('#') || line.startsWith('- ') || line.startsWith('* ') || line.startsWith('> ') || line.startsWith('```')) {
          const rendered = md.render(line)
          result.push(`<div class="diff-line diff-removed rendered">${rendered}</div>`)
        } else {
          result.push(`<div class="diff-line diff-removed">- ${escapeHtml(line)}</div>`)
        }
      }
    }
  })

  return result.join('\n')
}

export default {
  generateMarkdownDiff,
  computeCharDiff,
  escapeHtml,
  lcs,
}
