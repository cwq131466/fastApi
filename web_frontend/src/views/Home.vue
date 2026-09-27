<template>
  <div class="home-page">
    <div class="welcome-card">
      <h1>欢迎使用系统</h1>
      <p class="welcome-text">您好，{{ username }}！登录成功。</p>
      <div class="quick-actions">
        <el-card class="action-card" shadow="hover" @click="$router.push('/script')">
          <el-icon :size="40" color="#409EFF"><Document /></el-icon>
          <h3>运维脚本</h3>
          <p>查看和管理运维脚本</p>
        </el-card>
        <!-- <el-card class="action-card" shadow="hover">
          <el-icon :size="40" color="#67C23A"><Connection /></el-icon>
          <h3>交换机管理</h3>
          <p>管理网络设备</p>
        </el-card> -->
        <el-card class="action-card" shadow="hover" @click="$router.push('/docs')">
          <el-icon :size="40" color="#E6A23C"><Reading /></el-icon>
          <h3>运维文档</h3>
          <p>查看技术文档</p>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, Connection, Reading } from '@element-plus/icons-vue'

const username = ref(localStorage.getItem('username') || '用户')
</script>

<style scoped>
.home-page {
  padding: 24px;
  min-height: 100%;
}

.welcome-card {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.welcome-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 32px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.action-card {
  text-align: center;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-4px);
}

.action-card h3 {
  margin: 16px 0 8px;
  font-size: 18px;
  color: #303133;
}

.action-card p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}
</style>
