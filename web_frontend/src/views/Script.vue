<template>
  <div class="script-page">
    <!-- 左侧分类树 -->
    <div class="category-sidebar">
      <div class="sidebar-header">
        <h3>脚本分类</h3>
      </div>
      <el-tree
        ref="treeRef"
        :data="categoryTree"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        highlight-current
        default-expand-all
        @node-click="handleCategoryClick"
      />
    </div>

    <!-- 右侧脚本列表 -->
    <div class="script-content">
      <div class="content-header">
        <h2>{{ selectedCategory ? selectedCategory.name : '请选择分类' }}</h2>
      </div>

      <div v-if="selectedCategory" class="script-list-wrapper" v-loading="loading">
        <div v-if="scriptList.length > 0" class="card-list">
          <div
            v-for="script in scriptList"
            :key="script.id"
            class="script-card"
          >
            <!-- 卡片标题 -->
            <div class="card-header">
              <h3 class="card-title">{{ script.title }}</h3>
            </div>

            <!-- 卡片内容 -->
            <div class="card-body">
              <!-- 创建者和共享者信息（一行显示） -->
              <div class="info-row">
                <span class="info-label">创建者:</span>
                <el-tag v-if="script.creator_info" type="info" size="small">
                  {{ script.creator_info.alias || script.creator_info.username }}
                </el-tag>
                <span v-else style="color: #999; font-size: 12px;">未知</span>
                
                <span style="margin: 0 8px; color: #ddd;">|</span>
                
                <span class="info-label">共享给:</span>
                <div class="tags" style="display: inline-flex; margin-left: 4px;">
                  <el-tag
                    v-if="script.viewer_roles && script.viewer_roles.length > 0"
                    v-for="roleId in script.viewer_roles"
                    :key="roleId"
                    type="warning"
                    size="small"
                    style="margin-right: 4px;"
                  >
                    {{ getRoleName(roleId) }}
                  </el-tag>
                  <el-tag v-else type="success" size="small">所有角色</el-tag>
                </div>
              </div>

              <!-- 安装要求 -->
              <div v-if="script.requirements && script.requirements.length > 0" class="info-row">
                <span class="info-label">安装要求:</span>
                <div class="tags">
                  <el-tag
                    v-for="(req, idx) in script.requirements.slice(0, 5)"
                    :key="idx"
                    size="small"
                    type="info"
                  >
                    {{ req }}
                  </el-tag>
                  <el-tag v-if="script.requirements.length > 5" size="small">
                    +{{ script.requirements.length - 5 }}
                  </el-tag>
                </div>
              </div>

              <!-- 步骤数（可点击展开/折叠） -->
              <div class="info-row">
                <span class="info-label">步骤数:</span>
                <el-tag
                  type="success"
                  size="small"
                  style="cursor: pointer;"
                  @click="toggleSteps(script.id)"
                >
                  {{ getStepCount(script.steps) }} 个
                  <span v-if="getStepCount(script.steps) > 0">
                    {{ isExpanded(script.id) ? '▲' : '▼' }}
                  </span>
                </el-tag>
              </div>

              <!-- 主要功能 -->
              <div v-if="script.features" class="info-row">
                <span class="info-label">主要功能:</span>
                <p class="features-text">{{ script.features }}</p>
              </div>

              <!-- 安装步骤列表（默认折叠） -->
              <div
                v-if="script.steps && getStepCount(script.steps) > 0 && isExpanded(script.id)"
                class="steps-section"
              >
                <div class="steps-list">
                  <div
                    v-for="(step, idx) in getStepsArray(script.steps)"
                    :key="idx"
                    class="step-item"
                  >
                    <div class="step-content">
                      <div class="step-name">
                        <span class="step-number">{{ idx + 1 }}</span>
                        <span class="step-title">{{ step.key }}</span>
                      </div>
                      <div class="step-command-wrapper">
                        <pre class="step-command">{{ step.value }}</pre>
                        <el-button
                          size="small"
                          type="primary"
                          plain
                          @click="copySingleCommand(step.value, step.key, step.add_name)"
                          class="step-copy-btn"
                        >
                          <el-icon><CopyDocument /></el-icon>
                          复制
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty v-else description="暂无脚本数据" />

        <!-- 分页 -->
        <div v-if="scriptList.length > 0" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="pagination.pageSizes"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <div v-else class="empty-tip">
        <el-empty description="请从左侧选择分类查看脚本" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import { getCategoryTree, getScriptList } from '../api/script'
import { getUserInfo } from '../api/auth'
import axios from 'axios'

const treeRef = ref(null)
const categoryTree = ref([])
const selectedCategory = ref(null)
const scriptList = ref([])
const loading = ref(false)
const expandedScripts = ref(new Set())
const username = ref(localStorage.getItem('username') || '')
const roleOptions = ref([])

const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0,
  pageSizes: [10, 20, 50]
})

// 获取角色列表
async function fetchRoleList() {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/v1/role/list', {
      params: { page: 1, page_size: 100 },
      headers: { token }
    })
    roleOptions.value = (res.data.data?.items || res.data.data || []).map(role => ({
      label: role.name,
      value: role.id
    }))
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

// 根据角色ID获取角色名称
function getRoleName(roleId) {
  const role = roleOptions.value.find(r => r.value === roleId)
  return role ? role.label : `角色${roleId}`
}

// 获取分类树
async function fetchCategoryTree() {
  try {
    const res = await getCategoryTree()
    console.log('分类树响应:', res)
    // 修复：取 res.data.data 而不是 res.data
    categoryTree.value = res.data?.data || res.data || []
    
    // 如果有分类数据，自动选择第一个
    if (categoryTree.value.length > 0 && !selectedCategory.value) {
      selectedCategory.value = categoryTree.value[0]
      await fetchScriptList()
    }
  } catch (error) {
    console.error('获取分类失败:', error)
    const errorMsg = error.response?.data?.msg || error.response?.data?.detail || '获取分类失败'
    ElMessage.error(errorMsg)
    
    // 如果是认证错误，跳转到登录页
    if (error.response?.status === 401) {
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    }
  }
}

// 点击分类节点
function handleCategoryClick(node) {
  selectedCategory.value = node
  pagination.value.page = 1
  fetchScriptList()
}

// 获取脚本列表
async function fetchScriptList() {
  if (!selectedCategory.value) return

  loading.value = true
  try {
    const res = await getScriptList({
      category_id: selectedCategory.value.id,
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    console.log('脚本列表响应:', res)
    // 修复：正确处理响应数据
    scriptList.value = res.data?.data?.items || res.data?.items || res.data?.data || []
    pagination.value.total = res.data?.data?.total || res.data?.total || 0
  } catch (error) {
    console.error('获取脚本列表失败:', error)
    const errorMsg = error.response?.data?.msg || error.response?.data?.detail || '获取脚本列表失败'
    ElMessage.error(errorMsg)
    
    // 如果是认证错误，跳转到登录页
    if (error.response?.status === 401) {
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    }
  } finally {
    loading.value = false
  }
}

// 分页变化
function handlePageChange(page) {
  pagination.value.page = page
  fetchScriptList()
}

function handlePageSizeChange(pageSize) {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  fetchScriptList()
}

// 获取步骤数
function getStepCount(steps) {
  if (!steps) return 0
  if (Array.isArray(steps)) return steps.length
  return Object.keys(steps).length
}

// 将步骤转换为数组格式
function getStepsArray(steps) {
  if (!steps) return []
  if (Array.isArray(steps)) return steps
  return Object.entries(steps).map(([key, value]) => {
    // 如果 value 是对象，提取 value 字段
    if (typeof value === 'object' && value !== null && 'value' in value) {
      return {
        key,
        value: String(value.value),
        add_name: value.add_name || false
      }
    }
    // 如果 value 是字符串，直接使用
    return {
      key,
      value: String(value),
      add_name: false
    }
  })
}

// 切换步骤展开/折叠
function toggleSteps(scriptId) {
  if (expandedScripts.value.has(scriptId)) {
    expandedScripts.value.delete(scriptId)
  } else {
    expandedScripts.value.add(scriptId)
  }
}

// 检查是否展开
function isExpanded(scriptId) {
  return expandedScripts.value.has(scriptId)
}

// 复制单个命令
function copySingleCommand(command, stepName, addName = false) {
  let finalCommand = command
  
  // 如果 add_name 为 true，且存在 token，则添加 --token 参数
  const token = localStorage.getItem('token')
  if (addName && token) {
    finalCommand = `${command} --token ${token}`
  }
  
  // 兼容处理：检查 navigator.clipboard 是否可用
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(finalCommand).then(() => {
      const addedInfo = addName && token ? '（已添加 --token）' : ''
      ElMessage.success(`"${stepName}" 命令已复制到剪贴板${addedInfo}`)
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  } else {
    // 降级方案：使用传统方法复制
    const textarea = document.createElement('textarea')
    textarea.value = finalCommand
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      const addedInfo = addName && token ? '（已添加 --token）' : ''
      ElMessage.success(`"${stepName}" 命令已复制到剪贴板${addedInfo}`)
    } catch (err) {
      ElMessage.error('复制失败')
    }
    document.body.removeChild(textarea)
  }
}

// 获取用户信息
async function fetchUserInfo() {
  try {
    const res = await getUserInfo()
    if (res.data?.code === 200) {
      const userInfo = res.data.data || {}
      username.value = userInfo.username || localStorage.getItem('username') || ''
      // 更新 localStorage
      if (userInfo.username) {
        localStorage.setItem('username', userInfo.username)
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

onMounted(() => {
  fetchCategoryTree()
  fetchRoleList()
  fetchUserInfo()
})
</script>

<style scoped>
.script-page {
  display: flex;
  height: calc(100vh - 60px);
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
}

/* 左侧分类树 */
.category-sidebar {
  width: 240px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.sidebar-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #374151;
}

/* 右侧脚本内容 */
.script-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.content-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.content-header h2 {
  margin: 0;
  font-size: 18px;
  color: #1f2937;
}

.script-list-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.script-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.script-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409EFF;
}

.card-header {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.info-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
  min-width: 65px;
  flex-shrink: 0;
  padding-top: 2px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.features-text {
  margin: 0;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
  flex: 1;
}

/* 安装步骤区域 */
.steps-section {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-item {
  padding: 10px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.step-content {
  width: 100%;
}

.step-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: #409EFF;
  color: #fff;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.step-command-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.step-command {
  flex: 1;
  margin: 0;
  padding: 8px 10px;
  background: #1f2937;
  color: #10b981;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.step-copy-btn {
  flex-shrink: 0;
  height: 28px;
  font-size: 12px;
}

.empty-tip {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
}

/* Element Plus Tree 样式覆盖 */
:deep(.el-tree) {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 36px;
  border-radius: 4px;
}

:deep(.el-tree-node__content:hover) {
  background: #f5f7fa;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #ecf5ff;
  color: #409EFF;
}
</style>
