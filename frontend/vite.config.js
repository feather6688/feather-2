import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 配置文件
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',         // 强制 IPv4，避免 Windows localhost 解析问题
    port: 5173,                // 开发服务器端口
    open: false,               // 由后端 DrissionPage 统一打开浏览器
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
