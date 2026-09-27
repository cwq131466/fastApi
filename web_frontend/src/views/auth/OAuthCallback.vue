<template>
  <div class="oauth-callback">
    <div class="callback-box">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p class="loading-text">正在完成登录...</p>
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-result
          icon="error"
          title="登录失败"
          :sub-title="errorMessage"
        >
          <template #extra>
            <el-button type="primary" @click="goToLogin">返回登录</el-button>
          </template>
        </el-result>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')

// 处理OAuth回调
const handleCallback = async () => {
  try {
    const token = route.query.token
    
    if (!token) {
      throw new Error('未收到有效的认证令牌')
    }
    
    // 保存token和用户信息
    localStorage.setItem('token', token)
    
    // 获取用户信息（可选，如果需要可以调用后端接口）
    // await fetchUserInfo()
    
    ElMessage.success('登录成功')
    
    // 跳转到首页
    setTimeout(() => {
      router.push('/home')
    }, 500)
    
  } catch (err) {
    console.error('OAuth回调处理失败:', err)
    error.value = true
    errorMessage.value = err.message || '登录过程发生错误，请重试'
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

// 返回登录页
const goToLogin = () => {
  router.push('/login')
}

onMounted(() => {
  handleCallback()
})
</script>

<style scoped>
.oauth-callback {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.callback-box {
  width: 500px;
  min-height: 300px;
  padding: 40px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-container {
  text-align: center;
}

.loading-container .el-icon {
  font-size: 48px;
  color: #409EFF;
}

.loading-text {
  margin-top: 20px;
  font-size: 16px;
  color: #666;
}

.error-container {
  width: 100%;
}
</style>
