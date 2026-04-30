<template>
  <n-layout has-sider class="app-shell">
    <n-layout-sider bordered collapse-mode="width" :collapsed-width="64" :width="232" class="app-sider">
      <div class="brand">
        <div class="brand-mark">AI</div>
        <div class="brand-text">AI短剧</div>
      </div>
      <n-menu
        class="side-menu"
        :options="menuOptions"
        :value="activeKey"
        :default-expanded-keys="defaultExpandedKeys"
        @update:value="handleMenuChange"
      />
    </n-layout-sider>

    <n-layout class="app-main">
      <n-layout-header bordered class="app-header">
        <div>
          <div class="page-title">{{ pageTitle }}</div>
          <div class="page-subtitle">从内容策划、剧本打磨、AI分镜、多语种本地化，到素材上传、视频预览和投放分析的一体化 AI 短剧生产系统。</div>
        </div>
      </n-layout-header>

      <n-layout-content class="app-content">
        <!-- 内容区域由子路由渲染，保持布局和业务页面解耦。 -->
        <div class="content-shell">
          <router-view />
        </div>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import type { MenuOption } from 'naive-ui'
import { useAppStore } from '../stores/app'

type LeafMenu = {
  label: string
  key: string
  path: string
}

type MenuGroup = {
  label: string
  key: string
  children: LeafMenu[]
}

type MenuItem = LeafMenu | MenuGroup

const defaultExpandedKeys = ['ai-production', 'material-growth', 'media-assets-center', 'system-settings']

// 左侧菜单按真实业务域分组：生成页与结果列表页归属同一中心，页面职责仍保持分离。
const menus: MenuItem[] = [
  { label: '首页看板', key: 'dashboard', path: '/dashboard' },
  { label: '短剧项目管理', key: 'projects', path: '/projects' },
  {
    label: 'AI生产中心',
    key: 'ai-production',
    children: [
      { label: '内容策划', key: 'content-planning', path: '/content-planning' },
      { label: '剧本打磨', key: 'script-polish', path: '/script-polish' },
      { label: 'AI分镜制作', key: 'storyboard', path: '/storyboard' },
      { label: '分镜任务列表', key: 'storyboards', path: '/storyboards' },
      { label: '多语种本地化', key: 'localization', path: '/localization' },
      { label: '本地化版本列表', key: 'localizations', path: '/localizations' },
    ],
  },
  {
    label: '素材增长中心',
    key: 'material-growth',
    children: [
      { label: '广告素材生成', key: 'ad-materials', path: '/ad-materials' },
      { label: '广告素材库', key: 'ad-material-list', path: '/ad-materials/list' },
      { label: '增长分析', key: 'growth-analytics', path: '/growth-analytics' },
    ],
  },
  {
    label: '媒体资产中心',
    key: 'media-assets-center',
    children: [
      { label: '素材上传与预览', key: 'media-assets', path: '/media-assets' },
    ],
  },
  {
    label: '系统配置',
    key: 'system-settings',
    children: [
      { label: '字典管理', key: 'dictionary-management', path: '/settings/dictionaries' },
    ],
  },
]

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const flatMenus = computed<LeafMenu[]>(() => menus.flatMap((item) => ('children' in item ? item.children : [item])))

function renderLink(item: LeafMenu) {
  return () => h(RouterLink, { to: item.path }, { default: () => item.label })
}

const menuOptions = computed<MenuOption[]>(() => menus.map((item) => {
  if ('children' in item) {
    return {
      key: item.key,
      label: item.label,
      children: item.children.map((child) => ({
        key: child.key,
        label: renderLink(child),
      })),
    }
  }

  return {
    key: item.key,
    label: renderLink(item),
  }
}))

const activeKey = computed(() => {
  // 使用最长路径优先，避免 /ad-materials/list 被 /ad-materials 抢先匹配。
  const matched = [...flatMenus.value].sort((a, b) => b.path.length - a.path.length).find((item) => route.path.startsWith(item.path))
  return matched?.key ?? 'dashboard'
})

const pageTitle = computed(() => {
  const matched = flatMenus.value.find((item) => item.key === activeKey.value)
  return matched?.label ?? appStore.title
})

// 菜单切换使用路由跳转；分组节点没有 path，仅负责展开收起。
function handleMenuChange(key: string) {
  const target = flatMenus.value.find((item) => item.key === key)
  if (target) router.push(target.path)
}
</script>

<style scoped>
/* 后台工具型布局：强调清晰、稳定和可演示。 */
.app-shell {
  --app-sider-width: 232px;
  height: 100vh;
  min-height: 100vh;
  overflow: visible;
  background: #f5f7fb;
}

.app-sider {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 20;
  width: var(--app-sider-width) !important;
  height: 100vh;
  background: #ffffff;
}

.app-sider :deep(.n-layout-sider-scroll-container) {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-main {
  height: 100vh;
  margin-left: var(--app-sider-width);
  overflow-y: auto;
  background: #f5f7fb;
}

.brand {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 72px;
  padding: 0 18px;
  border-bottom: 1px solid #edf0f5;
  background: #ffffff;
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
  font-weight: 800;
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
  min-height: calc(100vh - 72px);
  padding: 24px;
  background: #f5f7fb;
}

.content-shell {
  width: 100%;
  box-sizing: border-box;
}

.side-menu {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 10px 18px;
}

.side-menu :deep(.n-menu-item-content) {
  border-radius: 8px;
}

.side-menu :deep(.n-menu-item-content--selected) {
  color: #0f9f5f;
  font-weight: 800;
}

.side-menu :deep(.n-menu-item-content-header) {
  font-size: 13px;
}

.side-menu :deep(.n-submenu .n-menu-item-content-header) {
  color: #374151;
}

.side-menu :deep(.n-menu .n-menu-item-content) {
  padding-left: 34px !important;
}
</style>
