import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/',  // 使用绝对路径，避免SPA路由下的资源加载问题
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true,
      }
    }
  }
})
