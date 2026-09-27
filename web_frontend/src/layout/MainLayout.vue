NEW_FILE_CODE
<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="header-left">
        <h2 class="logo">系统管理平台</h2>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          class="top-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/home">首页</el-menu-item>
          <el-menu-item index="/script">运维脚本</el-menu-item>
          <el-menu-item index="/scriptlogs">脚本日志</el-menu-item>
          <!-- <el-menu-item index="/switch">交换机管理</el-menu-item> -->
          <el-menu-item index="/docs">运维文档</el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand" trigger="click">
          <span class="user-info">
            <el-avatar :size="32" :src="displayAvatar" />
            <span class="username">{{ userInfo.username || username }}</span>
            <el-icon class="arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人信息
              </el-dropdown-item>
              <el-dropdown-item command="password">
                <el-icon><Lock /></el-icon>
                修改密码
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-wrapper">
      <router-view />
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="450px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="80px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Lock, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { getUserInfo, updatePassword, oauthLogout } from '../api/auth'
import { getAvatarUrl } from '../utils/avatar'

const router = useRouter()
const route = useRoute()

const username = ref(localStorage.getItem('username') || '')
const userInfo = ref({})
const passwordDialogVisible = ref(false)
const passwordFormRef = ref(null)

// 计算显示的头像（自定义或默认）
const displayAvatar = computed(() => {
  return getAvatarUrl(userInfo.value.avatar, userInfo.value.username || username.value)
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 当前激活的菜单
const activeMenu = computed(() => {
  const path = route.path
  
  // 如果路径以 /docs 开头（包括 /docs, /docs/tag, /docs/my-articles 等），都激活 /docs 菜单
  if (path.startsWith('/docs')) {
    return '/docs'
  }
  
  // 其他情况直接返回路径
  return path
})

// 获取用户信息
async function fetchUserInfo() {
  try {
    const res = await getUserInfo()
    // 响应拦截器已返回 response.data，所以 res 就是 { code, data, msg }
    if (res.code === 200) {
      userInfo.value = res.data || {}
      // 同步更新 localStorage 中的 username（OAuth2 登录后需要）
      if (userInfo.value.username) {
        localStorage.setItem('username', userInfo.value.username)
        username.value = userInfo.value.username
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 菜单选择
function handleMenuSelect(index) {
  if (index !== route.path) {
    router.push(index)
  }
}

// 下拉菜单命令处理
function handleCommand(command) {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'password':
      passwordDialogVisible.value = true
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 修改密码
async function handleChangePassword() {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const res = await updatePassword({
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword
        })
        
        if (res.data?.code === 200) {
          ElMessage.success('密码修改成功，请重新登录')
          passwordDialogVisible.value = false
          // 清空表单
          passwordForm.oldPassword = ''
          passwordForm.newPassword = ''
          passwordForm.confirmPassword = ''
          
          // 退出登录
          setTimeout(() => {
            handleLogout()
          }, 1500)
        } else {
          ElMessage.error(res.data?.msg || '密码修改失败')
        }
      } catch (error) {
        console.error('修改密码错误:', error)
        ElMessage.error(error.response?.data?.msg || '密码修改失败')
      }
    }
  })
}

// 退出登录
async function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 1. 调用后端 logout 接口
      // 后端会从 JWT token（请求头）中获取用户ID，然后从数据库获取 OAuth access_token 并回收
      const token = localStorage.getItem('token')
      if (token) {
        try {
          await oauthLogout()  // 不需要传参，后端从请求头获取 token
          console.log('后端登出成功')
        } catch (error) {
          console.warn('后端登出失败，继续执行本地登出:', error)
        }
      }
      
      // 2. 清除所有本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      sessionStorage.clear()
      
      ElMessage.success('已退出登录')
      
      // 3. 使用 replace 强制跳转，避免浏览器后退
      router.replace('/login')
      
      // 4. 延迟刷新页面，确保路由跳转完成
      setTimeout(() => {
        window.location.reload()
      }, 100)
    } catch (error) {
      console.error('登出过程出错:', error)
      // 即使出错也要确保本地数据被清除
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      sessionStorage.clear()
      router.replace('/login')
      window.location.reload()
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
.header {
  height: 60px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  z-index: 1000;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
  min-width: 0;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  color: #409EFF;
  margin: 0;
  white-space: nowrap;
  flex-shrink: 0;
}

.top-menu {
  border-bottom: none;
  background: transparent;
  flex: 1;
  min-width: 0;
}

:deep(.el-menu--horizontal) {
  border-bottom: none;
}

:deep(.el-menu--horizontal > .el-menu-item) {
  height: 60px;
  line-height: 60px;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  padding: 0 20px !important;
}

/* 隐藏更多按钮（折叠菜单） */
:deep(.el-menu--horizontal .el-sub-menu) {
  display: none !important;
}

:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  border-bottom-color: #409EFF;
  color: #409EFF;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #303133;
}

.arrow {
  font-size: 12px;
  color: #909399;
}

/* 主内容区 */
.main-wrapper {
  flex: 1;
  overflow-y: auto;
  background: #f5f7fa;
}
</style>