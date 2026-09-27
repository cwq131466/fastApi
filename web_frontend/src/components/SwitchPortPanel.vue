
<template>
  <div class="switch-port-panel">
    <!-- 设备信息 -->
    <div v-if="deviceInfo" class="device-info-section">
      <el-descriptions :column="4" size="small" border>
        <el-descriptions-item label="型号">{{ deviceInfo.model || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="运行时间">{{ deviceInfo.uptime || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item v-if="deviceInfo.cpu_usage" label="CPU使用率">
          {{ deviceInfo.cpu_usage }}
        </el-descriptions-item>
        <el-descriptions-item v-if="deviceInfo.memory_usage" label="内存使用率">
          {{ deviceInfo.memory_usage }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 端口表格 -->
    <div class="port-table-section">
      <el-table
        :data="ports"
        stripe
        style="width: 100%"
        height="500"
        :row-class-name="getRowClassName"
        @row-click="handleRowClick"
      >
        <el-table-column prop="name" label="端口" width="120" fixed>
          <template #default="{ row }">
            <span class="port-name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              :effect="row.status === 'adm' ? 'dark' : 'light'"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getPortTypeColor(row.port_type)" size="small">
              {{ getPortTypeText(row.port_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="pvid" label="PVID" width="70">
          <template #default="{ row }">
            <span>{{ row.pvid || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="dot1X" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.dot1x_enabled" type="danger" size="small">
              已启用
            </el-tag>
            <span v-else class="text-muted">未启用</span>
          </template>
        </el-table-column>

        <el-table-column label="MAC 地址" min-width="200">
          <template #default="{ row }">
            <div v-if="row.mac_addresses && row.mac_addresses.length > 0">
              <div
                v-for="(mac, idx) in row.mac_addresses"
                :key="idx"
                class="mac-address"
              >
                {{ mac.mac }}
                <span v-if="mac.vlan" class="vlan-tag">(VLAN {{ mac.vlan }})</span>
              </div>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="端口描述" min-width="150">
          <template #default="{ row }">
            <span>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.dot1x_enabled ? 'danger' : 'success'"
              size="small"
              @click.stop="handleToggleDot1x(row)"
            >
              {{ row.dot1x_enabled ? '关闭鉴权' : '开启鉴权' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 统计信息 -->
    <div class="port-stats">
      <el-tag type="success" size="small">活跃: {{ upCount }}</el-tag>
      <el-tag type="info" size="small">关闭: {{ downCount }}</el-tag>
      <el-tag type="danger" size="small">dot1X: {{ dot1xCount }}</el-tag>
      <el-tag type="warning" size="small">Trunk: {{ trunkCount }}</el-tag>
    </div>

    <!-- Jumpserver 登录对话框 -->
    <el-dialog
      v-model="loginDialogVisible"
      title="Jumpserver 身份验证"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入 Jumpserver 账号"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入 Jumpserver 密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="loginDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loginLoading" @click="handleLoginSubmit">
          验证
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ElTable, ElTableColumn, ElTag, ElDescriptions, ElDescriptionsItem, ElDialog, ElForm, ElFormItem, ElInput, ElButton } from 'element-plus'
import { togglePortDot1x } from '../api/asset'

const props = defineProps({
  ports: {
    type: Array,
    default: () => []
  },
  deviceInfo: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  highlightedPort: {
    type: Object,
    default: null
  },
  currentAssetId: {
    type: String,
    default: null
  },
  switchIp: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['port-click', 'update-ports'])

// Jumpserver 登录相关状态
const loginDialogVisible = ref(false)
const loginLoading = ref(false)
const loginFormRef = ref(null)
const currentPort = ref(null)

const loginForm = ref({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入 JumpServer 账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入 JumpServer 密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const upCount = computed(() => props.ports.filter(p => p.status === 'up').length)
const downCount = computed(() => props.ports.filter(p => p.status !== 'up').length)
const dot1xCount = computed(() => props.ports.filter(p => p.dot1x_enabled).length)
const trunkCount = computed(() => props.ports.filter(p => p.port_type === 'trunk').length)

function getRowClassName({ row }) {
  if (props.highlightedPort && row.name === props.highlightedPort.name) {
    return 'row-highlight'
  }
  if (row.dot1x_enabled) return 'row-dot1x'
  if (row.status === 'up') return 'row-up'
  return ''
}

function getStatusType(status) {
  if (status === 'up') return 'success'
  if (status === 'adm') return 'warning'
  return 'info'
}

function getStatusText(status) {
  const map = { up: '开启', down: '关闭', adm: '禁用' }
  return map[status] || status || '未知'
}

function getPortTypeColor(type) {
  if (type === 'trunk') return 'warning'
  if (type === 'access') return 'primary'
  return 'info'
}

function getPortTypeText(type) {
  const map = { access: 'Access', trunk: 'Trunk', hybrid: 'Hybrid' }
  return map[type] || type || '-'
}

function handleRowClick(row) {
  // 移除点击事件，不再弹出详情
}

// 处理切换 dot1X 鉴权
function handleToggleDot1x(row) {
  // 检查端口类型，trunk 口不允许开启或关闭鉴权
  if (row.port_type === 'trunk') {
    ElMessage.warning('Trunk 端口不支持 dot1X 鉴权操作')
    return
  }
  
  currentPort.value = row
  loginDialogVisible.value = true
  // 重置表单
  loginForm.value = {
    username: '',
    password: ''
  }
}

// 处理登录提交
async function handleLoginSubmit() {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      if (!props.switchIp) {
        ElMessage.error('未获取到交换机 IP 地址')
        return
      }
      
      loginLoading.value = true
      try {
        // 确定操作类型（开启或关闭）
        const enable = !currentPort.value.dot1x_enabled
        
        // 调用后端 API
        const response = await togglePortDot1x(
          props.switchIp,
          currentPort.value.name,
          {
            enable: enable,
            jumpserver_username: loginForm.value.username,
            jumpserver_password: loginForm.value.password
          }
        )
        
        if (response.data?.code === 200 || response.data?.success) {
          ElMessage.success(response.data?.data?.message || '操作成功')
          loginDialogVisible.value = false
          
          // 局部刷新：直接更新当前端口的 dot1x 状态
          const portIndex = props.ports.findIndex(p => p.name === currentPort.value.name)
          if (portIndex !== -1) {
            // 创建新的端口对象以触发响应式更新
            const updatedPort = { ...props.ports[portIndex] }
            updatedPort.dot1x_enabled = enable
            
            // 更新 ports 数组中的端口
            const newPorts = [...props.ports]
            newPorts[portIndex] = updatedPort
            
            // 通过 emit 通知父组件更新
            emit('update-ports', newPorts)
          }
        } else {
          ElMessage.error(response.data?.msg || response.data?.detail || '操作失败')
        }
      } catch (error) {
        console.error('切换 dot1x 状态失败:', error)
        const errorMsg = error.response?.data?.detail || error.message || '操作失败'
        ElMessage.error(errorMsg)
      } finally {
        loginLoading.value = false
      }
    }
  })
}
</script>

<style scoped>
.switch-port-panel {
  padding: 10px;
}

.device-info-section {
  margin-bottom: 16px;
}

.port-table-section {
  margin-bottom: 12px;
}

.port-name-cell {
  font-weight: 500;
  color: #303133;
}

.text-muted {
  color: #c0c4cc;
}

.mac-address {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #606266;
}

.vlan-tag {
  font-size: 11px;
  color: #909399;
  margin-left: 4px;
}

.port-stats {
  display: flex;
  gap: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  justify-content: center;
}

:deep(.row-up) {
  background-color: #f0f9ff !important;
}

:deep(.row-dot1x) {
  background-color: #fef0f0 !important;
}

:deep(.row-highlight) {
  background-color: #fdf6ec !important;
  border: 2px solid #e6a23c;
}

:deep(.el-table__row:hover) {
  cursor: pointer;
}
</style>