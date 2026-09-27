<script setup>
import { ref, onMounted, resolveDirective, h, computed } from 'vue'
import {
  NButton,
  NTag,
  NSpace,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NDynamicTags,
  NDynamicInput,
  NPopconfirm,
  NTreeSelect,
  useMessage,
  NCard,
  NPagination,
  NSpin,
  NModal,
  NUpload,
  NSwitch,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api/script'
import TheIcon from '@/components/icon/TheIcon.vue'
import { copyToClipboard } from '@/utils/common'
import { getToken } from '@/utils/auth/token'

defineOptions({ name: '运维脚本管理' })

const $message = useMessage()
const userStore = useUserStore()
const selectedCategory = ref(null)
const categoryTree = ref([])
const scriptList = ref([])
const loading = ref(false)
const expandedScripts = ref(new Set()) // 记录展开的脚本ID
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})
const vPermission = resolveDirective('permission')

// 判断用户是否有管理分类的权限（超级管理员或管理员角色）
const canManageCategory = computed(() => {
  // 超级管理员拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }
  
  // 检查是否有"管理员"角色
  const roles = userStore.role || []
  return roles.some(role => role.name === '管理员')
})

// 文件上传相关
const customFilename = ref('')
const uploadedFiles = ref([])
const uploadUrl = '/api/v1/script/upload/upload'
const uploadHeaders = computed(() => ({
  token: getToken(),
}))

// 分类管理相关
const categoryModalVisible = ref(false)
const categoryModalTitle = ref('')
const categoryForm = ref({ id: null, name: '', parent_id: 0, order: 0 })
const categoryFormRef = ref(null)
const categoryAction = ref('add') // 'add' or 'edit'

// 角色选项（用于权限选择器）
const roleOptions = ref([])

// 左侧分类树
async function fetchCategoryTree() {
  const res = await api.getCategoryTree()
  categoryTree.value = res.data
}

// 获取角色列表（用于权限选择器）
async function fetchRoleList() {
  try {
    const res = await api.getRoleList({ page: 1, page_size: 100 })
    roleOptions.value = (res.data?.items || res.data || []).map(role => ({
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

// 扁平化分类树（递归展开所有子分类）
function flattenCategories(categories, level = 0) {
  let result = []
  for (const cat of categories) {
    result.push({ ...cat, _level: level })
    if (cat.children && cat.children.length > 0) {
      result = result.concat(flattenCategories(cat.children, level + 1))
    }
  }
  return result
}

// 点击分类节点
function handleCategoryClick(node) {
  selectedCategory.value = node
  pagination.value.page = 1
  fetchScriptList()
}

// 添加分类
function handleAddCategory() {
  categoryAction.value = 'add'
  categoryModalTitle.value = '添加分类'
  categoryForm.value = { id: null, name: '', parent_id: 0, order: 0 }
  categoryModalVisible.value = true
}

// 编辑分类
function handleEditCategory(node) {
  categoryAction.value = 'edit'
  categoryModalTitle.value = '编辑分类'
  categoryForm.value = {
    id: node.id,
    name: node.name,
    parent_id: node.parent_id || 0,
    order: node.order || 0,
  }
  categoryModalVisible.value = true
}

// 删除分类
async function handleDeleteCategory(node) {
  try {
    await api.deleteCategory({ category_id: node.id })
    $message.success('删除成功')
    await fetchCategoryTree()
    if (selectedCategory.value?.id === node.id) {
      selectedCategory.value = null
      scriptList.value = []
    }
  } catch (error) {
    $message.error(error.response?.data?.msg || '删除失败')
  }
}

// 保存分类
async function handleSaveCategory() {
  if (!categoryForm.value.name) {
    $message.error('请输入分类名称')
    return
  }

  try {
    if (categoryAction.value === 'add') {
      await api.createCategory(categoryForm.value)
      $message.success('创建成功')
    } else {
      await api.updateCategory(categoryForm.value)
      $message.success('更新成功')
    }
    categoryModalVisible.value = false
    await fetchCategoryTree()
  } catch (error) {
    $message.error(error.response?.data?.msg || '操作失败')
  }
}

// 获取脚本列表
async function fetchScriptList() {
  if (!selectedCategory.value) return
  
  loading.value = true
  try {
    const res = await api.getScriptList({
      category_id: selectedCategory.value.id,
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    scriptList.value = res.data?.items || res.data || []
    pagination.value.total = res.data?.total || 0
  } catch (error) {
    $message.error(error.response?.data?.msg || '获取脚本列表失败')
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

// 右侧脚本 CRUD
const { modalVisible, modalAction, modalTitle, modalLoading, handleAdd, handleEdit, handleDelete,
        modalForm, modalFormRef } = useCRUD({
  name: '脚本',
  initForm: { requirements: [], steps: [], reference_links: [], order: 0 },
  doCreate: api.createScript,
  doUpdate: api.updateScript,
  doDelete: api.deleteScript,
  refresh: fetchScriptList,
})

// 重写 handleAdd，清空上传文件列表
function handleAddWithClear() {
  // 调用原始的 handleAdd
  handleAdd()
  
  // 清空已上传文件列表
  uploadedFiles.value = []
  
  // 清空自定义文件名
  customFilename.value = ''
}

// 创建新的步骤项
function createNewStep() {
  return { key: '', value: '', add_name: false }
}

// 自定义保存函数，转换数据格式
async function handleCustomSave() {
  if (!modalFormRef.value) return
  
  // 表单验证
  await new Promise((resolve, reject) => {
    modalFormRef.value.validate((errors) => {
      if (errors) {
        reject(new Error('Validation failed'))
      } else {
        resolve(true)
      }
    })
  }).catch(() => false)

  // 转换 steps 从数组到对象格式
  const submitData = { ...modalForm.value }
  
  // 如果 steps 是数组格式，转换为对象
  if (Array.isArray(submitData.steps)) {
    const stepsObj = {}
    submitData.steps.forEach(item => {
      if (item.key && item.value) {
        // 如果 add_name 为 true，保存为对象格式
        if (item.add_name) {
          stepsObj[item.key] = {
            value: item.value,
            add_name: true
          }
        } else {
          // 否则保存为简单字符串
          stepsObj[item.key] = item.value
        }
      }
    })
    submitData.steps = stepsObj
  }
  
  // 转换 reference_links 格式（如果需要）
  if (Array.isArray(submitData.reference_links)) {
    submitData.reference_links = submitData.reference_links.filter(link => link.title && link.url)
  }
  
  // 添加 uploaded_files 字段
  submitData.uploaded_files = uploadedFiles.value.map(f => f.file_path)

  try {
    modalLoading.value = true
    
    if (modalAction.value === 'add') {
      await api.createScript(submitData)
      $message.success('创建成功')
    } else if (modalAction.value === 'edit') {
      await api.updateScript(submitData)
      $message.success('更新成功')
    }
    
    modalVisible.value = false
    fetchScriptList()
  } catch (error) {
    console.error('Save error:', error)
    $message.error(error.response?.data?.msg || '操作失败')
  } finally {
    modalLoading.value = false
  }
}

// 将对象格式的 steps 转换为数组格式（用于编辑显示）
function convertStepsToArray(steps) {
  if (!steps || typeof steps !== 'object') return []
  if (Array.isArray(steps)) return steps
  
  return Object.entries(steps).map(([key, value]) => {
    // 如果 value 是对象，提取其中的字段
    if (typeof value === 'object' && value !== null) {
      return {
        key,
        value: String(value.value || ''),
        add_name: value.add_name || false
      }
    }
    // 如果 value 是字符串，使用默认值
    return {
      key,
      value: String(value),
      add_name: false
    }
  })
}

// 重写 handleEdit，转换 steps 格式
async function handleEditWithConversion(row) {
  // 先调用原始的 handleEdit
  handleEdit(row)
  
  // 然后转换 steps 格式为数组
  if (modalForm.value.steps && typeof modalForm.value.steps === 'object' && !Array.isArray(modalForm.value.steps)) {
    modalForm.value.steps = convertStepsToArray(modalForm.value.steps)
  }
  
  // 确保 reference_links 是数组
  if (!Array.isArray(modalForm.value.reference_links)) {
    modalForm.value.reference_links = []
  }
  
  // 确保 viewer_roles 是数组
  if (!Array.isArray(modalForm.value.viewer_roles)) {
    modalForm.value.viewer_roles = []
  }
  
  // 从后端加载该脚本关联的文件列表（包含详细元数据）
  try {
    const res = await api.getScriptFiles(row.id)
    uploadedFiles.value = (res.data || []).map(file => ({
      id: file.id,
      file_path: file.file_path,
      filename: file.filename,
      original_filename: file.original_filename,
      display_name: file.display_name || file.original_filename,
      size: file.file_size,
      file_type: file.file_type,
      created_at: file.created_at,
    }))
  } catch (error) {
    console.error('Failed to load script files:', error)
    uploadedFiles.value = []
  }
}

// 获取步骤数
function getStepCount(steps) {
  if (!steps) return 0
  if (Array.isArray(steps)) return steps.length
  return Object.keys(steps).length
}

// 将步骤转换为数组格式（用于展示）
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
function copySingleCommand(command, stepName) {
  copyToClipboard(command)
  $message.success(`"${stepName}" 命令已复制到剪贴板`)
}

// 删除成功后刷新列表
async function handleDeleteAndRefresh(params) {
  await handleDelete(params, false)
  fetchScriptList()
}

// ==================== 文件上传相关函数 ====================

// 处理文件上传完成
function handleUploadFinish({ file, event }) {
  try {
    const response = JSON.parse(event.target.response)
    if (response.code === 200) {
      // 统一数据结构，将 file_size 转换为 size，并添加 display_name
      const fileData = {
        ...response.data,
        size: response.data.file_size,
        display_name: response.data.display_name || response.data.original_filename,
      }
      uploadedFiles.value.push(fileData)
      $message.success('文件上传成功')
      customFilename.value = '' // 清空自定义文件名
    } else {
      $message.error(response.msg || '上传失败')
    }
  } catch (error) {
    console.error('Upload error:', error)
    $message.error('上传失败')
  }
}

// 处理上传错误
function handleUploadError({ event }) {
  console.error('Upload error:', event)
  // 检查是否为413文件大小超限错误
  if (event.target && event.target.status === 413) {
    $message.error('文件大小超过限制（最大500MB），请选择较小的文件')
    return
  }
  $message.error('文件上传失败，请检查网络连接')
}

// 删除已上传的文件
async function handleDeleteFile(file) {
  try {
    await api.deleteFile({ 
      file_path: file.file_path,
      script_id: modalForm.value.id || null, // 如果正在编辑脚本，传递 script_id
    })
    uploadedFiles.value = uploadedFiles.value.filter(f => f.file_path !== file.file_path)
    $message.success('文件删除成功')
  } catch (error) {
    $message.error(error.response?.data?.msg || '删除失败')
  }
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  fetchCategoryTree()
  fetchRoleList()
})
</script>

<template>
  <div class="script-container">
    <!-- 左侧分类树 -->
    <div class="category-sidebar">
      <div class="sidebar-header">
        <h3>脚本分类</h3>
        <NButton 
          v-if="canManageCategory"
          size="tiny" 
          type="primary" 
          @click="handleAddCategory"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-5">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>添加
        </NButton>
      </div>
      
      <!-- 自定义分类列表 -->
      <div class="custom-category-list">
        <div 
          v-for="category in flattenCategories(categoryTree)" 
          :key="category.id"
          class="category-item"
          :class="{ 'active': selectedCategory && selectedCategory.id === category.id }"
          @click="handleCategoryClick(category)"
        >
          <span class="category-name">{{ category.name }}</span>
          <div class="category-actions">
            <NButton 
              v-if="canManageCategory"
              text 
              size="tiny" 
              type="primary" 
              @click.stop="handleEditCategory(category)"
              title="编辑"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </NButton>
            <NPopconfirm 
              v-if="canManageCategory"
              @positive-click.stop="handleDeleteCategory(category)"
            >
              <template #trigger>
                <NButton text size="tiny" type="error" title="删除">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                  </svg>
                </NButton>
              </template>
              确定删除该分类吗？
            </NPopconfirm>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧脚本列表 -->
    <div class="script-content">
      <CommonPage show-footer :title="selectedCategory ? `${selectedCategory.name} - 脚本列表` : '请选择分类'">
        <template #action>
          <NButton
            v-if="selectedCategory"
            v-permission="'post/api/v1/script/create'"
            type="primary"
            @click="handleAddWithClear"
          >
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建脚本
          </NButton>
        </template>

        <div v-if="selectedCategory" class="script-list-wrapper">
          <NSpin :show="loading">
            <div v-if="scriptList.length > 0" class="card-list">
              <NCard
                v-for="script in scriptList"
                :key="script.id"
                class="script-card"
                :bordered="true"
                hoverable
              >
                <!-- 标题行 -->
                <div class="card-header">
                  <h3 class="card-title">{{ script.title }}</h3>
                  <div class="card-actions">
                    <NButton
                      v-permission="'post/api/v1/script/update'"
                      size="small"
                      type="info"
                      @click="handleEditWithConversion(script)"
                    >
                      <TheIcon icon="mdi:edit" :size="16" class="mr-5" />编辑
                    </NButton>
                    <NPopconfirm
                      v-permission="'delete/api/v1/script/delete'"
                      @positive-click="handleDeleteAndRefresh({ id: script.id })"
                    >
                      <template #trigger>
                        <NButton size="small" type="error">
                          <TheIcon icon="mdi:delete" :size="16" class="mr-5" />删除
                        </NButton>
                      </template>
                      确定删除吗?
                    </NPopconfirm>
                  </div>
                </div>

                <!-- 内容行 -->
                <div class="card-body">
                  <!-- 创建者信息 -->
                  <div class="info-row" v-if="script.creator_info">
                    <span class="info-label">创建者:</span>
                    <NTag type="info" size="small">
                      {{ script.creator_info.alias || script.creator_info.username }}
                    </NTag>
                  </div>

                  <!-- 共享者/查看权限 -->
                  <div class="info-row" v-if="script.viewer_roles && script.viewer_roles.length > 0">
                    <span class="info-label">共享给:</span>
                    <NSpace>
                      <NTag
                        v-for="roleId in script.viewer_roles"
                        :key="roleId"
                        type="warning"
                        size="small"
                      >
                        {{ getRoleName(roleId) }}
                      </NTag>
                    </NSpace>
                  </div>
                  <div class="info-row" v-else-if="script.viewer_roles && script.viewer_roles.length === 0">
                    <span class="info-label">共享给:</span>
                    <NTag type="success" size="small">所有角色</NTag>
                  </div>

                  <!-- 安装要求 -->
                  <div class="info-row" v-if="script.requirements && script.requirements.length > 0">
                    <span class="info-label">安装要求:</span>
                    <NSpace>
                      <NTag
                        v-for="(req, idx) in script.requirements.slice(0, 5)"
                        :key="idx"
                        type="info"
                        size="small"
                      >
                        {{ req }}
                      </NTag>
                      <NTag v-if="script.requirements.length > 5" type="default" size="small">
                        +{{ script.requirements.length - 5 }}
                      </NTag>
                    </NSpace>
                  </div>

                  <!-- 步骤数（可点击展开/折叠）和主要功能 -->
                  <div class="info-row">
                    <div class="info-item">
                      <span class="info-label">步骤数:</span>
                      <NTag
                        type="success"
                        size="small"
                        style="cursor: pointer; user-select: none;"
                        @click="toggleSteps(script.id)"
                      >
                        {{ getStepCount(script.steps) }} 个
                        <span v-if="getStepCount(script.steps) > 0" style="margin-left: 4px;">
                          {{ isExpanded(script.id) ? '▲' : '▼' }}
                        </span>
                      </NTag>
                    </div>
                  </div>

                  <!-- 主要功能 -->
                  <div class="info-row" v-if="script.features">
                    <span class="info-label">主要功能:</span>
                    <p class="features-text">{{ script.features }}</p>
                  </div>

                  <!-- 安装步骤列表（默认折叠，点击步骤数展开） -->
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
                            <NButton
                              size="small"
                              type="primary"
                              ghost
                              @click="copySingleCommand(step.value, step.key)"
                              class="step-copy-btn-inline"
                            >
                              <TheIcon icon="mdi:content-copy" :size="14" />
                              复制
                            </NButton>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </NCard>
            </div>

            <!-- 空状态 -->
            <NEmpty
              v-else
              description="暂无脚本数据"
              class="empty-state"
            />

            <!-- 分页 -->
            <div v-if="scriptList.length > 0" class="pagination-wrapper">
              <NPagination
                v-model:page="pagination.page"
                v-model:page-size="pagination.pageSize"
                :item-count="pagination.total"
                :page-sizes="pagination.pageSizes"
                show-size-picker
                @update:page="handlePageChange"
                @update:page-size="handlePageSizeChange"
              />
            </div>
          </NSpin>
        </div>

        <div v-else class="empty-tip">
          <NEmpty description="请从左侧选择分类查看脚本" />
        </div>
      </CommonPage>
    </div>

    <!-- 脚本编辑弹窗 -->
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleCustomSave" width="800px">
      <NForm ref="modalFormRef" :model="modalForm" label-placement="left" label-width="100">
        <NFormItem label="脚本标题" path="title" :rule="{ required: true, message: '请输入标题' }">
          <NInput v-model:value="modalForm.title" placeholder="如：配置麒麟APT源" />
        </NFormItem>

        <NFormItem label="所属分类" path="category_id" :rule="{ required: true, message: '请选择分类' }">
          <NTreeSelect
            v-model:value="modalForm.category_id"
            :options="categoryTree"
            key-field="id"
            label-field="name"
            default-expand-all
          />
        </NFormItem>

        <NFormItem label="查看权限" path="viewer_roles">
          <NSelect
            v-model:value="modalForm.viewer_roles"
            :options="roleOptions"
            multiple
            placeholder="不选表示所有角色可见"
            clearable
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            选择可以查看此脚本的角色，不选则所有角色都可见
          </div>
        </NFormItem>

        <NFormItem label="安装要求">
          <NDynamicTags v-model:value="modalForm.requirements" />
        </NFormItem>

        <NFormItem label="主要功能" path="features">
          <NInput v-model:value="modalForm.features" type="textarea" :rows="3" placeholder="描述脚本的主要功能" />
        </NFormItem>

        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" :min="0" />
        </NFormItem>

        <NFormItem label="安装步骤">
          <div class="steps-hint">
            <p style="color: #999; font-size: 12px; margin-bottom: 8px;">
              提示：每个步骤包含名称和命令，例如：<br/>
              步骤名称：一键部署<br/>
              执行命令：sudo bash &lt; &lt;(wget -qO - http://...)
            </p>
          </div>
          <NDynamicInput
            v-model:value="modalForm.steps"
            key-placeholder="步骤名称（如：一键部署）"
            value-placeholder="执行命令"
            :on-create="createNewStep"
          >
            <template #default="{ value }">
              <NSpace vertical style="width: 100%">
                <NInput v-model:value="value.key" placeholder="步骤名称" style="width: 100%" />
                <NInput v-model:value="value.value" type="textarea" placeholder="执行命令" style="width: 100%" :rows="2" />
                <NSpace align="center">
                  <NSwitch v-model:value="value.add_name" size="small">
                    <template #checked>是</template>
                    <template #unchecked>否</template>
                  </NSwitch>
                  <span style="font-size: 12px; color: #666;">复制时为脚本添加参数</span>
                </NSpace>
              </NSpace>
            </template>
          </NDynamicInput>
        </NFormItem>

        <!-- 文件上传部分 -->
        <NFormItem label="关联文件">
          <div class="file-upload-section">
            <NSpace vertical style="width: 100%">
              <!-- 上传表单 -->
              <NSpace align="center">
                <NInput
                  v-model:value="customFilename"
                  placeholder="自定义文件名（可选，留空使用原文件名）"
                  style="width: 250px"
                  clearable
                />
                <NUpload
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :data="{ custom_filename: customFilename, display_name: customFilename }"
                  :show-file-list="false"
                  @finish="handleUploadFinish"
                  @error="handleUploadError"
                >
                  <NButton type="primary">
                    <TheIcon icon="material-symbols:upload" :size="16" class="mr-5" />
                    选择文件上传
                  </NButton>
                </NUpload>
              </NSpace>
              
              <!-- 已上传文件列表 -->
              <div v-if="uploadedFiles.length > 0" class="uploaded-files">
                <div class="files-label">已上传文件：</div>
                <NSpace vertical style="margin-top: 8px">
                  <div
                    v-for="(file, index) in uploadedFiles"
                    :key="index"
                    class="file-item"
                  >
                    <div class="file-info">
                      <span class="file-display-name">{{ file.display_name || file.filename }}</span>
                      <span class="file-original" v-if="file.display_name && file.display_name !== file.original_filename">({{ file.original_filename }})</span>
                      <span class="file-size">({{ formatFileSize(file.size) }})</span>
                    </div>
                    <NButton
                      size="tiny"
                      type="error"
                      ghost
                      @click="handleDeleteFile(file)"
                    >
                      删除
                    </NButton>
                  </div>
                </NSpace>
              </div>
            </NSpace>
          </div>
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 分类编辑弹窗 -->
    <NModal v-model:show="categoryModalVisible" preset="card" :title="categoryModalTitle" style="width: 450px;">
      <NForm ref="categoryFormRef" :model="categoryForm" label-placement="left" label-width="80">
        <NFormItem label="分类名称" path="name" :rule="{ required: true, message: '请输入分类名称' }">
          <NInput v-model:value="categoryForm.name" placeholder="请输入分类名称" />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="categoryForm.order" :min="0" placeholder="数字越小越靠前" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="categoryModalVisible = false">取消</NButton>
          <NButton type="primary" @click="handleSaveCategory">确定</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.script-container {
  display: flex;
  height: calc(100vh - 120px);
  gap: 16px;
}

.category-sidebar {
  width: 260px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #374151;
}

/* 自定义分类列表 */
.custom-category-list {
  padding: 8px 0;
}

.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
  margin: 2px 0;
}

.category-item:hover {
  background: #f5f7fa;
}

.category-item.active {
  background: rgba(244, 81, 30, 0.1);
  color: #F4511E;
}

.category-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.category-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 8px;
}

.script-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  transition: all 0.3s ease;
}

.script-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  min-width: 70px;
  flex-shrink: 0;
}

.features-text {
  margin: 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
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
  gap: 12px;
}

.step-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.step-item:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
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
  width: 24px;
  height: 24px;
  background: #3b82f6;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-title {
  font-size: 14px;
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
  padding: 10px 12px;
  background: #1f2937;
  color: #10b981;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.step-copy-btn-inline {
  flex-shrink: 0;
  margin-top: 0;
  height: 32px;
}

.empty-tip {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.empty-state {
  padding: 60px 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  border-top: 1px solid #f0f0f0;
  margin-top: 16px;
}

.steps-hint {
  margin-bottom: 8px;
}

/* 文件上传区域样式 */
.file-upload-section {
  width: 100%;
}

.uploaded-files {
  margin-top: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.files-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.file-item:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 200px;
}

.file-name {
  font-size: 13px;
  color: #374151;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
}

.file-display-name {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.file-original {
  font-size: 12px;
  color: #9ca3af;
}

/* 上传表单样式 */
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-form-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-label {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
  min-width: 80px;
}

.custom-filename-input {
  width: 250px;
}

.filename-hint {
  font-size: 12px;
  color: #9ca3af;
  white-space: nowrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
