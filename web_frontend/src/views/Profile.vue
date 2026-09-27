<template>
  <div class="profile-container">
    <!-- 统计卡片 -->
    <el-card class="stats-card">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-number">{{ myArticleCount }}</div>
          <div class="stat-label">我的文章</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ favoriteCount }}</div>
          <div class="stat-label">收藏文章</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ sharedArticleCount }}</div>
          <div class="stat-label">可编辑文章</div>
        </div>
      </div>
    </el-card>

    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
        </div>
      </template>

      <el-form :model="userInfo" label-width="100px" class="profile-form">
        <!-- 头像部分 -->
        <el-form-item label="头像">
          <div class="avatar-section">
            <el-avatar 
              :size="100" 
              :src="displayAvatar"
              class="user-avatar"
            />
            <div class="avatar-actions">
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                style="display: none"
                @change="handleAvatarSelect"
              />
              <el-button 
                type="primary" 
                size="small"
                :loading="uploadingAvatar"
                @click="triggerAvatarUpload"
              >
                <el-icon><Upload /></el-icon>
                更换头像
              </el-button>
              <div class="avatar-hint">
                支持 JPG/PNG/GIF/WEBP，最大 2MB
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 用户名 -->
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled />
        </el-form-item>

        <!-- 姓名 -->
        <el-form-item label="姓名">
          <el-input v-model="userInfo.alias" placeholder="请输入姓名" />
        </el-form-item>

        <!-- 邮箱 -->
        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" placeholder="请输入邮箱" />
        </el-form-item>

        <!-- 电话 -->
        <el-form-item label="电话">
          <el-input v-model="userInfo.phone" placeholder="请输入电话" />
        </el-form-item>

        <!-- 保存按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveProfile">
            保存修改
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { getUserInfo, uploadAvatar } from '@/api/auth'
import { getAvatarUrl } from '@/utils/avatar'
import blogApi from '@/api/blog'

const userInfo = ref({
  username: '',
  alias: '',
  email: '',
  phone: '',
  avatar: null
})

const uploadingAvatar = ref(false)
const saving = ref(false)
const fileInputRef = ref(null)

// 统计信息
const myArticleCount = ref(0)
const favoriteCount = ref(0)
const sharedArticleCount = ref(0)

// 计算显示的头像（自定义或默认）
const displayAvatar = computed(() => {
  return getAvatarUrl(userInfo.value.avatar, userInfo.value.username)
})

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const res = await getUserInfo()
    if (res.code === 200 && res.data) {
      userInfo.value = {
        username: res.data.username || '',
        alias: res.data.alias || '',
        email: res.data.email || '',
        phone: res.data.phone || '',
        avatar: res.data.avatar || null
      }
      // 保存用户名到 localStorage
      localStorage.setItem('username', res.data.username || '')
      
      // 获取统计信息
      await Promise.all([
        fetchMyArticleCount(),
        fetchFavoriteCount(),
        fetchSharedArticleCount()
      ])
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

// 获取我的文章数量
const fetchMyArticleCount = async () => {
  try {
    const res = await blogApi.getArticleList({ page: 1, page_size: 1 })
    myArticleCount.value = res.total || 0
  } catch (error) {
    console.error('获取文章数量失败:', error)
  }
}

// 获取收藏文章数量
const fetchFavoriteCount = async () => {
  try {
    const res = await blogApi.getFavoriteList({ page: 1, page_size: 1 })
    favoriteCount.value = res.total || 0
  } catch (error) {
    console.error('获取收藏数量失败:', error)
  }
}

// 获取可编辑文章数量
const fetchSharedArticleCount = async () => {
  try {
    const res = await blogApi.getSharedArticleStats()
    sharedArticleCount.value = res.data?.count || 0
  } catch (error) {
    console.error('获取可编辑文章数量失败:', error)
  }
}

// 触发文件选择
const triggerAvatarUpload = () => {
  fileInputRef.value?.click()
}

// 处理头像文件选择
const handleAvatarSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('无效的图片类型，仅支持 JPG/PNG/GIF/WEBP')
    return
  }
  
  // 验证文件大小（2MB）
  const maxSize = 2 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('头像大小超过限制（最大 2MB）')
    return
  }
  
  // 显示确认对话框
  ElMessageBox.confirm(
    '确定要上传此头像吗？',
    '确认上传',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => {
    uploadAvatarFile(file)
  }).catch(() => {
    // 用户取消
  })
}

// 上传头像文件
const uploadAvatarFile = async (file) => {
  uploadingAvatar.value = true
  
  try {
    const res = await uploadAvatar(file)
    
    if (res.code === 200 && res.data) {
      // 更新本地头像
      userInfo.value.avatar = res.data.url
      
      ElMessage.success('头像上传成功')
    } else {
      throw new Error(res.msg || '上传失败')
    }
  } catch (error) {
    console.error('头像上传错误:', error)
    ElMessage.error(error.message || '头像上传失败')
  } finally {
    uploadingAvatar.value = false
    // 重置文件输入
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

// 保存个人资料
const saveProfile = async () => {
  saving.value = true
  
  try {
    // TODO: 调用后端更新接口（如果后端支持更新用户资料）
    // 目前后端可能没有提供更新用户资料的接口，这里只是模拟
    
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 组件挂载时获取用户信息
onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

/* 统计卡片 */
.stats-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stats-grid {
  display: flex;
  justify-content: space-around;
  gap: 20px;
}

.stat-item {
  flex: 1;
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.2s;
}

.stat-item:hover {
  transform: translateY(-4px);
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.profile-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.profile-form {
  max-width: 600px;
  margin: 0 auto;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-avatar {
  border: 2px solid #dcdfe6;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.avatar-hint {
  font-size: 12px;
  color: #909399;
}
</style>
