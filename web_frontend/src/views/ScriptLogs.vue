<template>
  <div class="script-logs-page">
    <!-- 查询条件区域 -->
    <div class="query-section">
      <el-form :inline="true" :model="queryParams" class="query-form">
        <el-form-item label="日志级别">
          <el-select
            v-model="queryParams.level"
            placeholder="请选择"
            clearable
            style="width: 140px"
          >
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
            <el-option label="DEBUG" value="DEBUG" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP地址">
          <el-input
            v-model="queryParams.ip"
            placeholder="请输入IP地址"
            clearable
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input
            v-model="queryParams.username"
            placeholder="请输入用户名"
            clearable
            style="width: 160px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="搜索日志信息"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="执行时间">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

     <!-- 日志列表 -->
      <div class="logs-content" v-loading="loading">
        <div v-if="logList.length > 0" class="log-table-container">
          <!-- 表头 -->
          <div class="log-table-header">
            <div class="log-col col-level">级别</div>
            <div class="log-col col-time">执行时间</div>
            <div class="log-col col-ip">IP地址</div>
            <div class="log-col col-username">用户</div>
            <div class="log-col col-os">系统</div>
            <div class="log-col col-info">日志信息</div>
            <div class="log-col col-cmd">命令</div>
            <div class="log-col col-mac">MAC</div>
          </div>
          
          <!-- 日志行 -->
          <div
            v-for="log in logList"
            :key="log.id"
            class="log-table-row"
          >
            <div class="log-col col-level">
              <el-tag :type="getLevelTagType(log.level)" size="small">
                {{ log.level }}
              </el-tag>
            </div>
            <div class="log-col col-time">{{ formatTime(log.time) }}</div>
            <div class="log-col col-ip">{{ log.ip || '-' }}</div>
            <div class="log-col col-username">{{ log.username || '-' }}</div>
            <div class="log-col col-os">{{ log.os || '-' }}</div>
            <div class="log-col col-info" :title="log.info">{{ truncateText(log.info, 50) }}</div>
            <div class="log-col col-cmd" :title="log.cmd">{{ truncateText(log.cmd, 40) }}</div>
            <div class="log-col col-mac">{{ log.mac || '-' }}</div>
          </div>
        </div>
      <!-- 空状态 -->
      <el-empty v-else description="暂无日志数据" />

      <!-- 分页 -->

        <!-- 分页 -->
        <div v-if="logList.length > 0" class="pagination-wrapper">
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getScriptLogList } from '../api/script'

const loading = ref(false)
const logList = ref([])
const dateRange = ref([])

const queryParams = reactive({
  level: '',
  ip: '',
  username: '',
  keyword: '',
  start_time: null,
  end_time: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
  pageSizes: [10, 20, 50]
})

// 获取日志级别标签类型
function getLevelTagType(level) {
  const types = {
    INFO: '',
    WARNING: 'warning',
    ERROR: 'danger',
    DEBUG: 'success'
  }
  return types[level] || ''
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  try {
    const date = new Date(time)
    const pad = (num) => num.toString().padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  } catch (e) {
    return time
  }
}

// 截断文本
function truncateText(text, maxLength) {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// 获取日志列表
async function fetchLogList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...queryParams
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0]
      params.end_time = dateRange.value[1]
    }

    const res = await getScriptLogList(params)
    logList.value = res.data?.data?.items || res.data?.data || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('获取日志列表失败:', error)
    
    // 检查是否是权限错误
    if (error.response?.status === 403 || error.response?.data?.msg?.includes('Permission denied')) {
      ElMessageBox.alert(
        '您没有查看脚本日志的权限。<br><br>此功能仅限<strong>网络运维人员</strong>访问，如需查看请联系系统管理员申请权限。',
        '权限不足',
        {
          confirmButtonText: '知道了',
          type: 'warning',
          dangerouslyUseHTMLString: true,
          customClass: 'permission-denied-dialog'
        }
      )
    } else {
      const errorMsg = error.response?.data?.msg || error.response?.data?.detail || '获取日志列表失败'
      ElMessage.error(errorMsg)

      if (error.response?.status === 401) {
        setTimeout(() => {
          window.location.href = '/login'
        }, 1500)
      }
    }
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchLogList()
}

// 重置
function handleReset() {
  queryParams.level = ''
  queryParams.ip = ''
  queryParams.username = ''
  queryParams.keyword = ''
  dateRange.value = []
  pagination.page = 1
  fetchLogList()
}

// 分页变化
function handlePageChange(page) {
  pagination.page = page
  fetchLogList()
}

function handlePageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  fetchLogList()
}

onMounted(() => {
  fetchLogList()
})
</script>

<style scoped>
.script-logs-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  padding: 16px;
  background: #f5f7fa;
  gap: 16px;
}

/* 查询区域 */
.query-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.query-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.query-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

/* 日志内容区域 */
.logs-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
}

.log-table-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
}

/* 表头样式 */
.log-table-header {
  display: grid;
  grid-template-columns: 80px 160px 130px 100px 250px minmax(150px, 1fr) minmax(150px, 1fr) 140px;
  background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
  border-bottom: 2px solid #e2e8f0;
  font-weight: 600;
  font-size: 13px;
  color: #475569;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.log-table-header .log-col {
  padding: 12px 10px;
  border-right: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.log-table-header .log-col:last-child {
  border-right: none;
}

/* 日志行样式 */
.log-table-row {
  display: grid;
  grid-template-columns: 80px 160px 130px 100px 250px minmax(200px, 1fr) minmax(150px, 1fr) 140px;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s ease;
  font-size: 13px;
}

.log-table-row:hover {
  background: #f8fafc;
  box-shadow: inset 0 0 0 1px #409EFF;
}

.log-table-row:nth-child(even) {
  background: #fafbfc;
}

.log-table-row:nth-child(even):hover {
  background: #f8fafc;
}

.log-col {
  padding: 10px;
  border-right: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-col:last-child {
  border-right: none;
}

/* 各列特定样式 */
.col-level {
  justify-content: center;
}

.col-time {
  color: #64748b;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  justify-content: center;
}

.col-ip {
  color: #409EFF;
  font-weight: 500;
  font-family: 'Consolas', 'Monaco', monospace;
  justify-content: center;
}

.col-username {
  color: #334155;
  justify-content: center;
}

.col-os {
  color: #64748b;
  justify-content: center;
}

.col-info {
  color: #1e293b;
  justify-content: flex-start;
  text-align: left;
}

.col-cmd {
  color: #10b981;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  justify-content: flex-start;
  text-align: left;
  background: #f0fdf4;
}

.col-mac {
  color: #64748b;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  justify-content: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px;
  border-top: 1px solid #e2e8f0;
  background: #fff;
  flex-shrink: 0;
}

/* 权限不足对话框样式 */
:deep(.permission-denied-dialog) {
  .el-message-box__header {
    background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
    color: white;
    border-radius: 4px 4px 0 0;
    
    .el-message-box__title {
      color: white;
      font-weight: 600;
    }
  }
  
  .el-message-box__content {
    padding: 24px;
    font-size: 15px;
    line-height: 1.8;
  }
  
  .el-message-box__btns {
    padding: 16px 24px 24px;
    
    .el-button--primary {
      background: #f59e0b;
      border-color: #f59e0b;
      
      &:hover {
        background: #d97706;
        border-color: #d97706;
      }
    }
  }
}
</style>
