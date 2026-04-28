<template>
  <div class="project-detail-page">
    <n-spin :show="loading">
      <template v-if="overview">
        <n-card bordered class="hero-card">
          <div class="hero-header">
            <div>
              <div class="eyebrow">短剧项目详情</div>
              <h2>{{ overview.project.name }}</h2>
              <p>{{ overview.project.description || '暂无项目简介' }}</p>
              <div class="status-summary">
                <span v-for="item in projectStatusSummary" :key="item.label">
                  {{ item.label }}：<strong>{{ item.value }}</strong>
                </span>
              </div>
            </div>
            <n-space>
              <n-button secondary @click="router.push('/projects')">返回项目列表</n-button>
              <n-button type="primary" @click="goNextStep">进入下一步生产</n-button>
            </n-space>
          </div>

          <n-grid :cols="6" :x-gap="12" :y-gap="12" responsive="screen" class="meta-grid">
            <n-grid-item v-for="item in projectMeta" :key="item.label" :span="1" :s-span="3">
              <div class="meta-item">
                <div class="meta-label">{{ item.label }}</div>
                <div class="meta-value">
                  <n-tag v-if="item.tag" :type="item.type" bordered>{{ item.value }}</n-tag>
                  <span v-else>{{ item.value }}</span>
                </div>
              </div>
            </n-grid-item>
          </n-grid>
        </n-card>

        <n-grid :cols="6" :x-gap="14" :y-gap="14" responsive="screen">
          <n-grid-item v-for="item in statCards" :key="item.label" :s-span="12">
            <n-card bordered class="stat-card">
              <n-statistic :label="item.label" :value="item.value" />
              <div class="stat-hint">{{ item.hint }}</div>
            </n-card>
          </n-grid-item>
        </n-grid>

        <n-card title="AI短剧生产链路" bordered>
          <div class="pipeline-grid">
            <div v-for="item in overview.pipeline" :key="item.key" class="pipeline-item" :class="item.status">
              <div class="pipeline-title-row">
                <span>{{ item.title }}</span>
                <n-tag :type="pipelineTagType(item.status)" bordered>{{ pipelineStatusText[item.status] }}</n-tag>
              </div>
              <div class="pipeline-count">{{ item.count }} 项资产</div>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </n-card>

        <n-card title="分集级生产提示" bordered class="episode-workbench-card">
          <div class="episode-workbench">
            <div>
              <div class="entry-title">AI分镜、本地化、媒体上传和单集广告素材建议从分集管理进入</div>
              <p>AI分镜、本地化、媒体上传和单集广告素材属于分集级生产，请先进入分集管理，选择具体集数后再操作。系统会携带 projectId、episodeId、episodeNo，让生成结果沉淀到对应分集。</p>
            </div>
            <n-button type="primary" @click="router.push(`/projects/${projectId}/episodes`)">进入分集管理</n-button>
          </div>
        </n-card>

        <n-grid :cols="2" :x-gap="14" :y-gap="14" responsive="screen">
          <n-grid-item :s-span="24">
            <n-card title="项目级规划" bordered class="entry-card">
              <p class="entry-section-desc">
                项目级用于整部短剧的策划、整体剧本、分集管理、项目级广告策略和增长分析；具体 AI分镜、本地化、媒体上传和单集广告素材请进入分集管理后按集操作。
              </p>
              <div class="entry-grid">
                <div v-for="entry in productionEntries" :key="entry.path" class="entry-item">
                  <div>
                    <div class="entry-title">{{ entry.label }}</div>
                    <p>{{ entry.description }}</p>
                  </div>
                  <n-button type="primary" secondary size="small" @click="goEntry(entry.path)">{{ entry.action }}</n-button>
                </div>
              </div>
            </n-card>
          </n-grid-item>
          <n-grid-item :s-span="24">
            <n-card title="项目级资产" bordered class="entry-card">
              <p class="entry-section-desc">这里查看的是整个项目下全部分集沉淀的资产，适合做统一审核、复用和投放复盘。</p>
              <div class="entry-grid">
                <div v-for="entry in assetEntries" :key="entry.path" class="entry-item">
                  <div>
                    <div class="entry-title">{{ entry.label }}</div>
                    <p>{{ entry.description }}</p>
                  </div>
                  <n-button secondary size="small" @click="goEntry(entry.path)">查看资产</n-button>
                </div>
              </div>
            </n-card>
          </n-grid-item>
        </n-grid>

        <n-grid :cols="3" :x-gap="14" :y-gap="14" responsive="screen">
          <n-grid-item v-for="section in recentSections" :key="section.title" :s-span="24">
            <n-card :title="section.title" bordered class="recent-card">
              <template #header-extra>
                <n-button size="small" secondary @click="goEntry(section.listPath)">查看全部</n-button>
              </template>
              <template v-if="section.items.length">
                <div
                  v-for="item in section.items"
                  :key="`${section.title}-${item.id}`"
                  class="recent-item clickable"
                  @click="goEntry(section.listPath)"
                >
                  <div>
                    <div class="recent-title">{{ item.title }}</div>
                    <div class="recent-meta">{{ item.type }} / {{ formatTime(item.created_at) }}</div>
                  </div>
                  <n-tag size="small" bordered>{{ item.status }}</n-tag>
                </div>
              </template>
              <n-empty v-else description="当前暂无数据，后续生成结果会沉淀到这里。">
                <template #extra>
                  <n-space class="empty-actions">
                    <n-button type="primary" secondary size="small" @click="goEntry(section.createPath)">
                      {{ section.createText }}
                    </n-button>
                    <n-button secondary size="small" @click="goEntry(section.listPath)">
                      {{ section.listText }}
                    </n-button>
                  </n-space>
                </template>
              </n-empty>
            </n-card>
          </n-grid-item>
        </n-grid>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { getProjectOverview } from '../api/projects'
import type { ProjectOverview, ShortDramaProjectPriority, ShortDramaProjectStage, ShortDramaProjectStatus } from '../types/project'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const overview = ref<ProjectOverview | null>(null)

const stageText: Record<ShortDramaProjectStage, string> = {
  planning: '策划中',
  scripting: '剧本中',
  storyboard: '分镜中',
  localization: '本地化中',
  material: '素材制作中',
  launch: '投放中',
  completed: '已完成',
}

const statusText: Record<ShortDramaProjectStatus, string> = {
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
  archived: '已归档',
}

const priorityText: Record<ShortDramaProjectPriority, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

const pipelineStatusText = {
  completed: '已完成',
  processing: '进行中',
  pending: '待开始',
}

const productionEntries = [
  { label: '内容策划', path: '/content-planning', description: '生成整部短剧的题材、人设、卖点和剧情大纲', action: '进入策划' },
  { label: '剧本打磨', path: '/script-polish', description: '用于整体剧本大纲、核心冲突、节奏和前三秒钩子优化', action: '进入打磨' },
  { label: '分集管理', path: '/projects/{projectId}/episodes', description: '按集推进 AI分镜、本地化、媒体和单集广告素材生产', action: '进入分集' },
  { label: '项目级广告策略', path: '/ad-materials', description: '生成整部短剧级别的广告方向、Hook、CTA 和封面提示词', action: '进入策略' },
  { label: '增长分析', path: '/growth-analytics', description: '查看整部短剧的 CTR、CVR、ROI 等投放效果', action: '查看分析' },
]

const assetEntries = [
  { label: '分镜任务列表', path: '/storyboards', description: '查看该项目下全部分集的分镜任务。' },
  { label: '本地化版本列表', path: '/localizations', description: '查看该项目下全部分集的本地化版本。' },
  { label: '广告素材库', path: '/ad-materials/list', description: '查看项目级和分集级广告素材。' },
  { label: '媒体资产列表', path: '/media-assets', description: '查看该项目下所有分集的媒体资产。' },
]

const projectId = computed(() => String(route.params.id || ''))

const projectMeta = computed(() => {
  const project = overview.value?.project
  if (!project) return []
  return [
    { label: '题材类型', value: project.genre },
    { label: '目标市场', value: project.target_market },
    { label: '主语言', value: project.language },
    { label: '计划集数', value: `${project.episode_count} 集` },
    { label: '当前阶段', value: stageText[project.stage], tag: true, type: 'info' },
    { label: '项目状态', value: statusText[project.status], tag: true, type: project.status === 'active' ? 'success' : 'default' },
    { label: '优先级', value: priorityText[project.priority], tag: true, type: project.priority === 'high' ? 'error' : 'warning' },
    { label: '负责人', value: project.owner || '-' },
    { label: '创建时间', value: formatTime(project.created_at) },
    { label: '更新时间', value: formatTime(project.updated_at) },
  ]
})

const statCards = computed(() => {
  const stats = overview.value?.stats
  if (!stats) return []
  return [
    { label: '分集数量', value: stats.episode_count ?? overview.value?.project.episode_count ?? 0, hint: '项目下已建立的单集生产单元' },
    { label: '内容策划', value: stats.content_plan_count, hint: '项目下已沉淀的策划方案' },
    { label: '剧本版本', value: stats.script_count, hint: '剧本打磨与优化版本' },
    { label: '分镜任务', value: stats.storyboard_count, hint: '可生产化 AI 分镜数量' },
    { label: '本地化版本', value: stats.localization_count, hint: '目标市场语言适配版本' },
    { label: '广告素材', value: stats.ad_material_count, hint: '投放标题、钩子和文案' },
    { label: '媒体资产', value: stats.media_asset_count, hint: '视频、图片、字幕等素材' },
  ]
})

const projectStatusSummary = computed(() => {
  const project = overview.value?.project
  const stats = overview.value?.stats
  if (!project || !stats) return []
  return [
    { label: '计划', value: `${project.episode_count} 集` },
    { label: '已建', value: `${stats.episode_count ?? 0} 集` },
    { label: '当前阶段', value: stageText[project.stage] },
  ]
})

const recentSections = computed(() => {
  if (!overview.value) return []
  return [
    {
      title: '最近分镜',
      items: overview.value.recent_storyboards,
      listPath: '/storyboards',
      createPath: '/projects/{projectId}/episodes',
      createText: '去分集管理',
      listText: '查看分镜列表',
    },
    {
      title: '最近广告素材',
      items: overview.value.recent_ad_materials,
      listPath: '/ad-materials/list',
      createPath: '/ad-materials',
      createText: '去生成广告素材',
      listText: '查看素材库',
    },
    {
      title: '最近媒体资产',
      items: overview.value.recent_media_assets,
      listPath: '/media-assets',
      createPath: '/projects/{projectId}/episodes',
      createText: '去分集管理',
      listText: '查看媒体资产',
    },
  ]
})

function pipelineTagType(status: 'completed' | 'processing' | 'pending') {
  if (status === 'completed') return 'success'
  if (status === 'processing') return 'warning'
  return 'default'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function goEntry(path: string) {
  const target = path.replace('{projectId}', projectId.value)
  // 项目详情页同时承载项目级入口和分集级入口：项目级页面带 query，分集管理使用真实路径参数。
  if (target.includes('?') || target.startsWith(`/projects/${projectId.value}`)) {
    router.push(target)
    return
  }
  router.push(`${target}?projectId=${projectId.value}`)
}

function goNextStep() {
  // 项目详情页只跳项目级规划入口；进入分镜、本地化、媒体等单集操作时，统一先去分集管理选择集数。
  const stage = overview.value?.project.stage
  const pathMap: Record<string, string> = {
    planning: '/content-planning',
    scripting: '/script-polish',
    storyboard: '/projects/{projectId}/episodes',
    localization: '/projects/{projectId}/episodes',
    material: '/projects/{projectId}/episodes',
    launch: '/growth-analytics',
    completed: '/growth-analytics',
  }
  goEntry(pathMap[stage || 'planning'] || '/content-planning')
}

async function loadOverview() {
  if (!projectId.value) {
    message.error('项目 ID 不存在')
    router.push('/projects')
    return
  }
  loading.value = true
  try {
    const res = await getProjectOverview(projectId.value)
    if (res.code === 0) {
      overview.value = res.data
    }
  } catch {
    message.error('项目不存在或项目总览加载失败')
    router.push('/projects')
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<style scoped>
.project-detail-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.project-detail-page :deep(.n-spin-content) {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-detail-page :deep(.n-card) {
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
}

.hero-card {
  background: linear-gradient(135deg, #f8fafc, #eef6ff);
}

.hero-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow {
  margin-bottom: 6px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
}

.hero-header h2 {
  margin: 0;
  color: #111827;
  font-size: 24px;
}

.hero-header p {
  max-width: 780px;
  margin: 10px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.status-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.status-summary span {
  padding: 6px 10px;
  color: #4b5563;
  font-size: 12px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
}

.status-summary strong {
  color: #111827;
}

.meta-grid {
  margin-top: 20px;
}

.meta-item {
  min-height: 72px;
  padding: 12px;
  border: 1px solid #edf0f5;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
}

.meta-label {
  color: #6b7280;
  font-size: 12px;
}

.meta-value {
  margin-top: 8px;
  color: #111827;
  font-weight: 700;
  word-break: break-word;
}

.stat-card {
  min-height: 124px;
}

.stat-hint {
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
}

.pipeline-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(140px, 1fr));
  gap: 12px;
  overflow-x: auto;
}

.pipeline-item {
  min-width: 140px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f8fafc;
}

.pipeline-item.completed {
  border-color: rgba(24, 160, 88, 0.24);
  background: #f0fdf4;
}

.pipeline-item.processing {
  border-color: rgba(245, 158, 11, 0.28);
  background: #fffbeb;
}

.pipeline-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: #111827;
  font-weight: 800;
}

.pipeline-count {
  margin-top: 12px;
  color: #2563eb;
  font-size: 18px;
  font-weight: 800;
}

.pipeline-item p {
  margin: 8px 0 0;
  color: #4b5563;
  font-size: 12px;
  line-height: 1.6;
}

.entry-card {
  min-height: 100%;
}

.episode-workbench-card {
  background: #fbfcff;
}

.episode-workbench {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  min-width: 0;
}

.episode-workbench p {
  max-width: 820px;
  margin: 8px 0 0;
  color: #6b7280;
  line-height: 1.7;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.entry-section-desc {
  margin: 0 0 14px;
  color: #4b5563;
  line-height: 1.7;
}

.entry-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  min-height: 112px;
  padding: 14px;
  border: 1px solid #edf0f5;
  border-radius: 10px;
  background: #fbfcff;
}

.entry-title {
  color: #111827;
  font-weight: 800;
}

.entry-item p {
  margin: 8px 0 0;
  color: #6b7280;
  line-height: 1.6;
  word-break: break-word;
}

.recent-card {
  min-height: 260px;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #edf0f5;
}

.recent-item.clickable {
  cursor: pointer;
}

.recent-item.clickable:hover .recent-title {
  color: #18a058;
}

.recent-item:last-child {
  border-bottom: 0;
}

.recent-title {
  color: #111827;
  font-weight: 700;
}

.recent-meta {
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
}

.empty-actions {
  margin-top: 10px;
}

@media (max-width: 900px) {
  .hero-header {
    flex-direction: column;
  }

  .entry-grid {
    grid-template-columns: 1fr;
  }

  .episode-workbench {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
