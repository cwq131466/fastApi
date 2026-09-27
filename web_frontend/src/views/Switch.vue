<template>
  <div class="switch-container">
    <!-- 顶部导航栏 -->
    <el-header class="app-header">
      <div class="header-left">
        <el-icon :size="28" color="#409eff"><Monitor /></el-icon>
        <h1 class="app-title">交换机管理</h1>
      </div>
      <div class="header-right">
        <el-tag v-if="healthStatus" :type="healthStatus.mock_data_enabled ? 'warning' : 'success'" size="small">
          {{ healthStatus.mock_data_enabled ? '模拟数据' : '真实API' }}
        </el-tag>
        <el-button size="small" @click="showHealthDialog">
          <el-icon><InfoFilled /></el-icon>
          状态
        </el-button>
      </div>
    </el-header>

    <!-- 主要内容区域 - 左右布局 -->
    <el-container class="main-container" :class="{ 'disabled': portLoading }">
      <!-- 左侧资产列表 -->
      <el-aside width="200px" class="asset-list-panel">
        <div class="asset-list-container">
          <!-- 搜索框 -->
          <div class="search-box">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索主机名、IP..."
              clearable
              size="small"
              :disabled="portLoading"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <!-- 资产列表 -->
          <div class="asset-list" v-loading="loading">
            <el-scrollbar height="calc(100vh - 170px)">
              <div
                v-for="asset in assetList"
                :key="asset.id"
                class="asset-item"
                :class="{ active: currentAsset?.id === asset.id, disabled: portLoading }"
                @click="!portLoading && handleSelectAsset(asset)"
              >
                <div class="asset-info">
                  <div class="asset-row">
                    <span class="asset-name">{{ asset.name }}</span>
                    <span class="asset-ip">{{ asset.address }}</span>
                  </div>
                  <div class="asset-row-sub">
                    <span class="asset-category">{{ asset.category?.label || '-' }}</span>
                    <span class="asset-platform">{{ asset.platform?.name || '-' }}</span>
                  </div>
                  <div class="asset-labels" v-if="asset.labels && asset.labels.length > 0">
                    <el-tag
                      v-for="(label, idx) in asset.labels.slice(0, 3)"
                      :key="idx"
                      size="small"
                      type="info"
                      effect="plain"
                      style="margin-right: 4px"
                    >
                      {{ label }}
                    </el-tag>
                    <span v-if="asset.labels.length > 3" class="more-labels">+{{ asset.labels.length - 3 }}</span>
                  </div>
                </div>
              </div>

              <!-- 空状态 -->
              <el-empty
                v-if="!loading && assetList.length === 0"
                description="暂无网络设备资产"
                :image-size="60"
              />
            </el-scrollbar>
          </div>

          <!-- 分页 -->
          <div class="pagination-box" v-if="totalPages > 1">
            <el-pagination
              size="small"
              layout="prev, pager, next"
              :total="totalCount"
              :page-size="pageSize"
              :current-page="currentPage"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </el-aside>

      <!-- 右侧资产详情 -->
      <el-main class="asset-detail-panel">
        <!-- 加载遮罩层 -->
        <div v-if="portLoading" class="loading-overlay">
          <div class="loading-content">
            <el-icon class="is-loading" :size="50" color="#409eff"><Loading /></el-icon>
            <p class="loading-overlay-text">{{ loadingPhase }}</p>
            <el-progress 
              :percentage="loadingProgress" 
              :show-text="false"
              :stroke-width="6"
              striped
              striped-flow
              style="width: 300px; margin-top: 20px;"
            />
          </div>
        </div>

        <div class="asset-detail-container" :class="{ 'disabled': portLoading }">
          <!-- 未选中资产时的提示 -->
          <el-empty
            v-if="!currentAsset && !portLoading"
            description="请从左侧选择一个交换机查看详情"
            :image-size="80"
          />

          <!-- 资产详情 -->
          <div v-else-if="currentAsset" class="detail-content">
            <!-- 资产标题 -->
            <div class="detail-header">
              <h2 class="asset-title">
                <el-icon :size="20" color="#409eff"><Monitor /></el-icon>
                {{ currentAsset.name }}
              </h2>
            </div>

            <!-- 基本信息卡片 -->
            <el-card class="detail-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <el-icon><InfoFilled /></el-icon>
                  <span>基本信息</span>
                </div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="设备名称">
                  {{ currentAsset.name }}
                </el-descriptions-item>
                <el-descriptions-item label="IP地址">
                  <el-text type="primary">{{ currentAsset.address }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="分类">
                  {{ currentAsset.category?.label || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="平台">
                  {{ currentAsset.platform?.name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="标签" v-if="currentAsset.labels && currentAsset.labels.length > 0">
                  <el-tag
                    v-for="(label, idx) in currentAsset.labels"
                    :key="idx"
                    size="small"
                    style="margin-right: 4px"
                  >
                    {{ label }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="备注" v-if="currentAsset.comment">
                  {{ currentAsset.comment }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 端口状态卡片 -->
            <el-card class="detail-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <el-icon><Connection /></el-icon>
                  <span>端口状态</span>
                </div>
              </template>

              <!-- MAC 地址搜索 -->
              <div class="mac-search-box">
                <el-input
                  v-model="macSearchKeyword"
                  placeholder="输入 MAC 地址查找端口..."
                  clearable
                  size="small"
                  @input="handleMacSearch"
                  style="max-width: 350px"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <span v-if="searchResult" class="search-result">
                  找到端口: <strong>{{ searchResult.name }}</strong>
                </span>
                <span v-else-if="macSearchKeyword" class="search-result search-not-found">
                  未找到匹配的端口
                </span>
              </div>

              <!-- 端口面板 -->
              <SwitchPortPanel
                :ports="switchPorts"
                :device-info="deviceInfo"
                :loading="portLoading"
                :highlighted-port="searchResult"
                :current-asset-id="currentAsset?.id"
                :switch-ip="currentAsset?.address"
                @update-ports="handleUpdatePorts"
              />
            </el-card>
          </div>
        </div>
      </el-main>
    </el-container>

    <!-- 健康检查对话框 -->
    <el-dialog
      v-model="healthDialogVisible"
      title="系统状态"
      width="500px"
    >
      <el-descriptions :column="1" border v-if="healthStatus">
        <el-descriptions-item label="服务状态">
          <el-tag :type="healthStatus.status === 'healthy' ? 'success' : 'danger'">
            {{ healthStatus.status === 'healthy' ? '正常' : '异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="JumpServer连接">
          <el-tag :type="healthStatus.jumpserver_connected ? 'success' : 'info'">
            {{ healthStatus.jumpserver_connected ? '已连接' : '未连接' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据源">
          <el-tag :type="healthStatus.mock_data_enabled ? 'warning' : 'success'">
            {{ healthStatus.mock_data_enabled ? '模拟数据' : '真实API' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="详细信息">
          {{ healthStatus.message || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="healthDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>


  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, InfoFilled, Connection, Search, Loading } from '@element-plus/icons-vue'
import { getAssets, getSwitchPortsStream, healthCheck, togglePortDot1x } from '../api/asset'
import SwitchPortPanel from '../components/SwitchPortPanel.vue'
import { showGlobalLoading, updateLoadingText, closeGlobalLoading } from '../utils/loading'

// 资产列表状态
const loading = ref(false)
const assetList = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const searchKeyword = ref('')
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// 当前选中的资产
const currentAsset = ref(null)

// 端口状态
const portLoading = ref(false)
const switchPorts = ref([])
const deviceInfo = ref(null)
const loadingPhase = ref('')

// MAC 地址搜索
const macSearchKeyword = ref('')
const searchResult = ref(null)

// 端口详情弹窗


// 健康状态
const healthDialogVisible = ref(false)
const healthStatus = ref(null)

// 计算加载进度
const loadingProgress = computed(() => {
  if (!portLoading.value) return 0
  const phaseMap = {
    '正在登录交换机...': 30,
    '正在解析配置信息...': 60,
    '数据加载完成': 100,
    '加载失败': 0
  }
  return phaseMap[loadingPhase.value] || 10
})

// 获取健康状态
async function fetchHealth() {
  try {
    const res = await healthCheck()
    if (res.data?.code === 200) {
      healthStatus.value = res.data.data
    }
  } catch (error) {
    console.error('获取健康状态失败:', error)
  }
}

function showHealthDialog() {
  healthDialogVisible.value = true
}

// 获取资产列表
async function fetchAssets() {
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    if (searchKeyword.value) params.keyword = searchKeyword.value

    const res = await getAssets(params)
    if (res.data?.code === 200) {
      assetList.value = res.data.data.results || []
      totalCount.value = res.data.data.count || 0
    } else {
      ElMessage.error(res.data?.msg || '获取资产列表失败')
    }
  } catch (error) {
    console.error('获取资产列表错误:', error)
    ElMessage.error(error.response?.data?.msg || '获取资产列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchAssets()
}

async function handlePageChange(page) {
  currentPage.value = page
  await fetchAssets()
}

async function handleSelectAsset(asset) {
  currentAsset.value = asset
  await loadSwitchPorts(asset.id)
  macSearchKeyword.value = ''
  searchResult.value = null
}

const loadSwitchPorts = async (assetId) => {
  portLoading.value = true
  loadingPhase.value = '正在登录交换机...'
  switchPorts.value = []
  deviceInfo.value = null

  let eventSource = null
  
  try {
    // 显示全局加载遮罩
    showGlobalLoading('正在连接交换机...', 0)

    // 使用 SSE 流式获取数据
    eventSource = getSwitchPortsStream(assetId, {
      onProgress: (phase, message) => {
        console.log(`[进度] ${phase}: ${message}`)
        loadingPhase.value = message
        updateLoadingText(message)
      },
      onComplete: (result) => {
        if (result.success) {
          const data = result.data
          deviceInfo.value = data.device_info
          switchPorts.value = data.ports || []
          loadingPhase.value = '数据加载完成'
          updateLoadingText('数据加载完成')
          
          // 延迟关闭，让用户看到完成状态
          setTimeout(() => {
            closeGlobalLoading()
          }, 500)
          
          ElMessage.success('端口信息加载成功')
        } else {
          loadingPhase.value = '加载失败'
          closeGlobalLoading()
          ElMessage.error(result.error || '获取端口信息失败')
        }
      },
      onError: (error) => {
        loadingPhase.value = '加载失败'
        closeGlobalLoading()
        console.error('SSE 错误:', error)
        ElMessage.error(error.error || '获取端口信息失败')
      }
    })
    
  } catch (error) {
    loadingPhase.value = '加载失败'
    closeGlobalLoading()
    console.error('获取端口信息错误:', error)
    ElMessage.error(error.response?.data?.msg || '获取端口信息失败')
  } finally {
    portLoading.value = false
  }
}

function handleMacSearch(keyword) {
  if (!keyword || !keyword.trim()) {
    searchResult.value = null
    return
  }
  searchResult.value = findPortByMac(keyword.trim()) || null
}

function findPortByMac(macAddress) {
  const normalizedMac = macAddress.toLowerCase().replace(/[-:]/g, '')
  for (const port of switchPorts.value) {
    if (port.mac_addresses && port.mac_addresses.length > 0) {
      for (const macInfo of port.mac_addresses) {
        const normalizedInfoMac = macInfo.mac.toLowerCase().replace(/[-:]/g, '')
        if (normalizedInfoMac.includes(normalizedMac) || normalizedMac.includes(normalizedInfoMac)) {
          return port
        }
      }
    }
  }
  return null
}

// 处理切换 dot1X 鉴权
async function handleToggleDot1x({ port, credentials }) {
  console.log('切换 dot1X 鉴权:', port.name, credentials)
  
  if (!currentAsset.value) {
    ElMessage.warning('请先选择一个设备')
    return
  }
  
  try {
    // 调用后端 API 切换 dot1X 状态
    await togglePortDot1x(currentAsset.value.id, port.name, credentials)
    
    // 更新本地端口状态
    const targetPort = switchPorts.value.find(p => p.name === port.name)
    if (targetPort) {
      targetPort.dot1x_enabled = !targetPort.dot1x_enabled
      ElMessage.success(`端口 ${port.name} 鉴权已${targetPort.dot1x_enabled ? '开启' : '关闭'}`)
    }
  } catch (error) {
    console.error('切换 dot1X 失败:', error)
    ElMessage.error('操作失败：' + (error.message || '未知错误'))
  }
}

function getStatusText(status) {
  const map = { up: '开启', down: '关闭', adm: '禁用' }
  return map[status] || status || '未知'
}

function getPortTypeText(type) {
  const map = { access: 'Access', trunk: 'Trunk', hybrid: 'Hybrid' }
  return map[type] || type || '-'
}

// 局部更新端口列表（只更新 dot1x 状态）
function handleUpdatePorts(newPorts) {
  switchPorts.value = newPorts
}

onMounted(() => {
  fetchHealth()
  fetchAssets()
})
</script>

<style scoped>
.switch-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-title {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-container {
  flex: 1;
  overflow: hidden;
}

.asset-list-panel {
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  overflow: hidden;
}

.asset-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-box {
  padding: 8px 10px;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.asset-list {
  flex: 1;
  overflow: hidden;
}

.asset-item {
  padding: 6px 12px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.asset-item:hover:not(.disabled) {
  background-color: #f5f7fa;
}

.asset-item.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.asset-item.active {
  background-color: #ecf5ff;
  border-left: 3px solid #409eff;
}

.asset-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.asset-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-name {
  font-weight: 500;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.asset-ip {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
}

.asset-row-sub {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-category {
  font-size: 11px;
  color: #909399;
}

.asset-platform {
  font-size: 11px;
  color: #67c23a;
}

.asset-labels {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 2px;
}

.more-labels {
  font-size: 10px;
  color: #909399;
}

.pagination-box {
  padding: 6px 10px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.asset-detail-panel {
  padding: 0;
  overflow-y: auto;
  background-color: #f5f7fa;
}

.asset-detail-container {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
}

.loading-overlay-text {
  margin: 20px 0;
  font-size: 18px;
  color: #303133;
  font-weight: 500;
}

.disabled {
  pointer-events: none;
  opacity: 0.5;
}

.detail-content {
  max-width: 1200px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px 14px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.asset-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #303133;
}

.detail-card {
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.mac-search-box {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-result {
  font-size: 13px;
  color: #606266;
}

.search-result strong {
  color: #409eff;
}

.search-not-found {
  color: #f56c6c;
}

:deep(.el-descriptions__label) {
  width: 80px;
  font-weight: 500;
  font-size: 13px;
}

:deep(.el-descriptions__content) {
  font-size: 13px;
}
</style>
