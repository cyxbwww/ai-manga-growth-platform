<template>
  <n-layout has-sider class="app-shell">
    <n-layout-sider bordered collapse-mode="width" :collapsed-width="64" :width="232">
      <div class="brand">
        <div class="brand-mark">AI</div>
        <div class="brand-text">AI短剧</div>
      </div>
      <n-menu :options="menuOptions" :value="activeKey" @update:value="handleMenuChange" />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="app-header">
        <div>
          <div class="page-title">{{ pageTitle }}</div>
          <div class="page-subtitle">从内容策划、剧本打磨、AI分镜、多语种本地化，到素材上传、视频预览和投放分析的一体化 AI 短剧生产系统。</div>
        </div>
      </n-layout-header>

      <n-layout-content class="app-content">
        <!-- 内容区域由子路由渲染，保持布局和业务页面解耦。 -->
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import type { MenuOption } from 'naive-ui'
import { useAppStore } from '../stores/app'

// 菜单数据：覆盖从内容生产、素材上传到投放分析的完整演示链路。
const menus = [
  { label: '首页看板', key: 'dashboard', path: '/dashboard' },
  { label: '内容策划', key: 'content-planning', path: '/content-planning' },
  { label: '剧本打磨', key: 'script-polish', path: '/script-polish' },
  { label: 'AI分镜制作', key: 'storyboard', path: '/storyboard' },
  { label: '多语种本地化', key: 'localization', path: '/localization' },
  { label: '海外投放素材', key: 'ad-materials', path: '/ad-materials' },
  { label: '素材上传与预览', key: 'media-assets', path: '/media-assets' },
  { label: '增长分析', key: 'growth-analytics', path: '/growth-analytics' },
]

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const menuOptions: MenuOption[] = menus.map((item) => ({
  key: item.key,
  label: () => h(RouterLink, { to: item.path }, { default: () => item.label }),
}))

const activeKey = computed(() => {
  const matched = menus.find((item) => route.path.startsWith(item.path))
  return matched?.key ?? 'dashboard'
})

const pageTitle = computed(() => {
  const matched = menus.find((item) => item.key === activeKey.value)
  return matched?.label ?? appStore.title
})

// 菜单切换：使用路由跳转，保证刷新后状态可恢复。
function handleMenuChange(key: string) {
  const target = menus.find((item) => item.key === key)
  if (target) router.push(target.path)
}
</script>

<style scoped>
/* 后台工具型布局：强调清晰、稳定和可演示。 */
.app-shell {
  min-height: 100vh;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 64px;
  padding: 0 18px;
  border-bottom: 1px solid #edf0f5;
}

.brand-mark {
  display: grid;
  width: 34px;
  height: 34px;
  color: #ffffff;
  font-weight: 700;
  border-radius: 8px;
  background: #2563eb;
  place-items: center;
}

.brand-text {
  color: #111827;
  font-size: 16px;
  font-weight: 700;
}

.app-header {
  display: flex;
  align-items: center;
  height: 72px;
  padding: 0 28px;
  background: #ffffff;
}

.page-title {
  color: #111827;
  font-size: 20px;
  font-weight: 700;
}

.page-subtitle {
  margin-top: 4px;
  color: #6b7280;
  font-size: 13px;
}

.app-content {
  padding: 24px;
}
</style>
