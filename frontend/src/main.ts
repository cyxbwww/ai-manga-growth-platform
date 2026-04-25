import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import './styles.css'

// 应用入口：挂载路由、状态管理和 Naive UI。
createApp(App).use(createPinia()).use(router).use(naive).mount('#app')
