import { defineStore } from 'pinia'

// 全局应用状态：当前仅保留平台名称，后续可扩展用户、权限、主题等状态。
export const useAppStore = defineStore('app', {
  state: () => ({
    title: 'AI短剧制作平台 Demo',
  }),
})
