<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>用户登录</h2>
        <p>欢迎使用系统</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '账 号 登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- OAuth2 统一认证登录 -->
      <div class="oauth-section">
        <el-divider>或</el-divider>
        <el-button
          type="success"
          size="large"
          :loading="oauthLoading"
          class="oauth-btn"
          @click="handleOAuthLogin"
        >
          <el-icon><SwitchButton /></el-icon>
          统一认证登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SwitchButton } from '@element-plus/icons-vue'
import { login } from '../api/auth'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const oauthLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await login(loginForm.username, loginForm.password)
        console.log('[Login] Response:', response)
        
        // 响应拦截器已经提取了 data，所以 response 就是 {code: 200, msg: 'OK', data: {...}}
        let token = null
        let username = null
        let msg = '登录失败'
        
        // 检查 code 是否为 200
        if (response && response.code === 200) {
          // 从 response.data 中获取 token 和 username
          if (response.data) {
            token = response.data.access_token || response.data.token
            username = response.data.username || response.data.user?.username
            msg = response.msg || response.data.msg || '登录成功'
          }
        }
        
        if (token) {
          // 存储token
          localStorage.setItem('token', token)
          if (username) {
            localStorage.setItem('username', username)
          }
          
          ElMessage.success(msg)
          
          // 跳转到首页
          setTimeout(() => {
            router.push('/home')
          }, 500)
        } else {
          ElMessage.error(response?.msg || response?.message || '登录失败：未获取到token')
        }
      } catch (error) {
        console.error('登录错误:', error)
        ElMessage.error(error.response?.data?.msg || error.message || '登录失败，请检查网络连接')
      } finally {
        loading.value = false
      }
    }
  })
}

// OAuth2 统一认证登录
const handleOAuthLogin = () => {
  oauthLoading.value = true
  ElMessage.info('正在跳转到统一认证服务...')
  
  // 直接跳转到后端OAuth2登录接口
  window.location.href = '/api/v1/auth/oauth2/login'
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 420px;
  padding: 40px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 35px;
}

.login-header h2 {
  color: #409EFF;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.login-header p {
  color: #909399;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}

.login-btn {
  width: 100%;
  font-size: 16px;
  letter-spacing: 2px;
}

.oauth-section {
  margin-top: 15px;
}

.oauth-btn {
  width: 100%;
  font-size: 16px;
  letter-spacing: 2px;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409EFF inset;
}
</style>
