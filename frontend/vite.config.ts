import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 配置：接入 Vue 插件，保持第一阶段工程尽量简单。
export default defineConfig({
  plugins: [vue()],
})
