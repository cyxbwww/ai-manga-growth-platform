import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import ContentPlanning from '../views/ContentPlanning.vue'
import ScriptPolish from '../views/ScriptPolish.vue'
import Storyboard from '../views/Storyboard.vue'
import Localization from '../views/Localization.vue'
import AdMaterials from '../views/AdMaterials.vue'
import MediaAssets from '../views/MediaAssets.vue'
import GrowthAnalytics from '../views/GrowthAnalytics.vue'
import PlaceholderPage from '../views/PlaceholderPage.vue'

// 路由配置：覆盖从内容生产、素材管理到投放分析的完整演示链路。
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'Dashboard', component: Dashboard, meta: { title: '首页看板' } },
        { path: 'content-planning', name: 'ContentPlanning', component: ContentPlanning, meta: { title: '内容策划' } },
        { path: 'script-polish', name: 'ScriptPolish', component: ScriptPolish, meta: { title: '剧本打磨' } },
        { path: 'storyboard', name: 'Storyboard', component: Storyboard, meta: { title: 'AI分镜制作' } },
        { path: 'localization', name: 'Localization', component: Localization, meta: { title: '多语种本地化' } },
        { path: 'ad-materials', name: 'AdMaterials', component: AdMaterials, meta: { title: '海外投放素材' } },
        { path: 'media-assets', name: 'MediaAssets', component: MediaAssets, meta: { title: '素材上传与预览' } },
        { path: 'growth-analytics', name: 'GrowthAnalytics', component: GrowthAnalytics, meta: { title: '增长分析' } },
        { path: 'ad-assets', redirect: '/ad-materials' },
        { path: 'growth-analysis', redirect: '/growth-analytics' },
        { path: ':module', name: 'Placeholder', component: PlaceholderPage, meta: { title: '功能预留' } },
      ],
    },
  ],
})

export default router
