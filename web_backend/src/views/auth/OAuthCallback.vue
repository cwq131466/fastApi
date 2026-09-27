<template>
  <div class="oauth-callback">
    <div class="callback-box">
      <div v-if="loading" class="loading-container">
        <n-spin size="large" />
        <p class="loading-text">正在完成登录...</p>
      </div>

      <div v-else-if="error" class="error-container">
        <n-result
          status="error"
          title="登录失败"
          :description="errorMessage"
        >
          <template #footer>
            <n-button type="primary" @click="goToLogin">返回登录</n-button>
          </template>
        </n-result>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { setToken } from '@/utils'
import { addDynamicRoutes } from '@/router'

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

    // 保存token
    setToken(token)

    // 触发用户信息获取和动态路由加载
    await addDynamicRoutes()

    $message.success('登录成功')

    // 跳转到首页
    setTimeout(() => {
      router.push('/workbench')
    }, 500)

  } catch (err) {
    console.error('OAuth回调处理失败:', err)
    error.value = true
    errorMessage.value = err.message || '登录过程发生错误，请重试'
    $message.error(errorMessage.value)
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

.loading-container :deep(.n-spin) {
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
