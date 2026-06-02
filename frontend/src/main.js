/**
 * Vue3 应用入口
 */
import { createApp } from 'vue'
import App from './App.vue'

console.log('[启动] Vue 应用开始加载...')

const app = createApp(App)

// 全局错误捕获（用于调试）
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue 全局错误]', err)
  console.error('[出错组件]', instance?.$options?.__name || instance?.$.type?.__name || '未知')
  console.error('[错误详情]', info)
}

app.mount('#app')
console.log('[启动] Vue 应用挂载完成')
