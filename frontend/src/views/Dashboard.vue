<template>
  <div class="dashboard">
    <n-spin :show="loading">
      <n-alert v-if="errorText" type="error" :bordered="false">
        {{ errorText }}
      </n-alert>

      <n-card bordered class="hero-card">
        <div class="hero-content">
          <div>
            <div class="eyebrow">AI短剧生产工作台</div>
            <h2>AI短剧生产工作台</h2>
            <p>从短剧项目、分集生产、AI分镜、本地化、媒体资产到广告素材，统一查看生产进度和资产沉淀情况。</p>
          </div>
          <n-space>
            <n-button type="primary" @click="router.push('/projects')">进入短剧项目管理</n-button>
            <n-button secondary @click="router.push('/growth-analytics')">查看增长分析</n-button>
          </n-space>
        </div>
      </n-card>

      <n-grid :cols="6" :x-gap="14" :y-gap="14" responsive="screen">
        <n-grid-item v-for="item in metricCards" :key="item.label" :s-span="12">
          <n-card bordered class="metric-card">
            <div class="metric">{{ item.value }}</div>
            <div class="metric-label">{{ item.label }}</div>
            <div class="hint">{{ item.hint }}</div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid :cols="2" :x-gap="14" :y-gap="14" responsive="screen">
        <n-grid-item :s-span="24">
          <n-card title="项目生产阶段分布" bordered>
            <div class="stage-grid">
              <div v-for="item in stageCards" :key="item.key" class="stage-item">
                <n-tag :type="item.type" bordered>{{ item.label }}</n-tag>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </n-card>
        </n-grid-item>

        <n-grid-item :s-span="24">
          <n-card title="分集生产状态" bordered>
            <div class="stage-grid">
              <div v-for="item in episodeStatusCards" :key="item.label" class="stage-item">
                <n-tag :type="item.type" bordered>{{ item.label }}</n-tag>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid :cols="2" :x-gap="14" :y-gap="14" responsive="screen">
        <n-grid-item :s-span="24">
          <n-card title="最近项目" bordered class="list-card">
            <template v-if="summary.recentProjects.length">
              <div v-for="project in summary.recentProjects" :key="project.id" class="list-row clickable" @click="goProject(project.id)">
                <div class="row-main">
                  <div class="row-title">{{ project.name }}</div>
                  <div class="row-meta">{{ project.genre }} / {{ project.target_market }} / {{ formatTime(project.updated_at) }}</div>
                </div>
                <n-space size="small">
                  <n-tag :type="stageTagType(project.stage)" bordered>{{ projectStageText[project.stage] || project.stage }}</n-tag>
                  <n-tag :type="project.status === 'active' ? 'success' : 'default'" bordered>{{ projectStatusText[project.status] || project.status }}</n-tag>
                  <n-button size="small" secondary @click.stop="goProject(project.id)">进入详情</n-button>
                </n-space>
              </div>
            </template>
            <n-empty v-else description="暂无短剧项目，创建项目后会展示在这里。">
              <template #extra>
                <n-button type="primary" secondary @click="router.push('/projects')">去创建项目</n-button>
              </template>
            </n-empty>
          </n-card>
        </n-grid-item>

        <n-grid-item :s-span="24">
          <n-card title="最近分集" bordered class="list-card">
            <template v-if="summary.recentEpisodes.length">
              <div v-for="episode in summary.recentEpisodes" :key="episode.id" class="list-row clickable" @click="goEpisodes(episode.project_id)">
                <div class="row-main">
                  <div class="row-title">{{ episode.project_name }} / 第 {{ episode.episode_no }} 集：{{ episode.title }}</div>
                  <div class="row-meta">更新于 {{ formatTime(episode.updated_at) }}</div>
                </div>
                <n-space size="small">
                  <n-tag :type="episodeStageTagType(episode.stage)" bordered>{{ episodeStageText[episode.stage] || episode.stage }}</n-tag>
                  <n-tag bordered>分镜 {{ subStatusText(episode.storyboard_status) }}</n-tag>
                  <n-tag bordered>本地化 {{ subStatusText(episode.localization_status) }}</n-tag>
                  <n-tag bordered>媒体 {{ subStatusText(episode.media_status) }}</n-tag>
                  <n-button size="small" secondary @click.stop="goEpisodes(episode.project_id)">进入分集管理</n-button>
                </n-space>
              </div>
            </template>
            <n-empty v-else description="暂无分集数据，进入项目详情后可批量生成分集。">
              <template #extra>
                <n-button type="primary" secondary @click="router.push('/projects')">进入项目管理</n-button>
              </template>
            </n-empty>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-card title="生产链路说明" bordered>
        <div class="chain">
          <div v-for="item in chainItems" :key="item.key" class="chain-item">
            <div class="chain-title">{{ item.title }}</div>
            <p>{{ item.description }}</p>
          </div>
        </div>
        <n-alert type="info" :bordered="false" class="chain-note">
          projectId 负责整部短剧的项目归属；episodeId 负责具体某一集的生产归属；生成页负责生产，列表页负责资产沉淀，项目详情页和分集管理页负责生产调度。
        </n-alert>
      </n-card>

      <n-card title="AI 状态" bordered>
        <div v-if="aiStatus" class="ai-status">
          <div>
            <div class="status-title">{{ aiStatus.enabled ? '真实 AI 已启用' : '当前为 mock/fallback 模式' }}</div>
            <div class="status-copy">
              Provider：{{ aiStatus.provider }} · 模型：{{ aiStatus.model }} · API Key：{{ aiStatus.hasApiKey ? '已配置' : '未配置' }}
            </div>
            <div class="status-copy">Base URL：{{ aiStatus.baseUrl }}</div>
          </div>
          <n-tag :type="aiStatus.enabled ? 'success' : 'warning'" bordered>
            {{ aiStatus.enabled ? 'DeepSeek' : 'Fallback' }}
          </n-tag>
        </div>
        <n-empty v-else description="AI 状态加载中" />
      </n-card>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { getAiStatus } from '../api/ai'
import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { AiStatus } from '../types/ai'

type ProjectStage = 'planning' | 'scripting' | 'storyboard' | 'localization' | 'material' | 'launch' | 'completed'
type EpisodeStage = 'planning' | 'scripting' | 'storyboard' | 'localization' | 'media' | 'completed'

type RecentProject = {
  id: number
  name: string
  genre: string
  target_market: string
  stage: ProjectStage
  status: string
  updated_at: string
}

type RecentEpisode = {
  id: number
  project_id: number
  project_name: string
  episode_no: number
  title: string
  stage: EpisodeStage
  storyboard_status: string
  localization_status: string
  media_status: string
  updated_at: string
}

type DashboardSummary = {
  projectTotal: number
  episodeTotal: number
  storyboardTotal: number
  localizationTotal: number
  mediaAssetTotal: number
  adMaterialTotal: number
  projectStageDistribution: Record<ProjectStage, number>
  episodeStatus: {
    episodeTotal: number
    pendingStoryboard: number
    completedStoryboard: number
    completedLocalization: number
    uploadedMedia: number
    completedEpisodes: number
  }
  recentProjects: RecentProject[]
  recentEpisodes: RecentEpisode[]
}

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const errorText = ref('')
const aiStatus = ref<AiStatus | null>(null)

const summary = reactive<DashboardSummary>({
  projectTotal: 0,
  episodeTotal: 0,
  storyboardTotal: 0,
  localizationTotal: 0,
  mediaAssetTotal: 0,
  adMaterialTotal: 0,
  projectStageDistribution: {
    planning: 0,
    scripting: 0,
    storyboard: 0,
    localization: 0,
    material: 0,
    launch: 0,
    completed: 0,
  },
  episodeStatus: {
    episodeTotal: 0,
    pendingStoryboard: 0,
    completedStoryboard: 0,
    completedLocalization: 0,
    uploadedMedia: 0,
    completedEpisodes: 0,
  },
  recentProjects: [],
  recentEpisodes: [],
})

const projectStageText: Record<ProjectStage, string> = {
  planning: '策划中',
  scripting: '剧本中',
  storyboard: '分镜中',
  localization: '本地化中',
  material: '素材制作中',
  launch: '投放中',
  completed: '已完成',
}

const projectStatusText: Record<string, string> = {
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
  archived: '已归档',
}

const episodeStageText: Record<EpisodeStage, string> = {
  planning: '策划中',
  scripting: '剧本中',
  storyboard: '分镜中',
  localization: '本地化中',
  media: '媒体制作中',
  completed: '已完成',
}

const metricCards = computed(() => [
  { label: '短剧项目数', value: summary.projectTotal, hint: '当前系统中的短剧项目数量' },
  { label: '分集数量', value: summary.episodeTotal, hint: '所有项目下的分集数量' },
  { label: 'AI分镜数', value: summary.storyboardTotal, hint: '已沉淀的分镜任务数量' },
  { label: '本地化版本数', value: summary.localizationTotal, hint: '已生成的多语种本地化版本' },
  { label: '媒体资产数', value: summary.mediaAssetTotal, hint: '视频、图片、字幕等媒体资产' },
  { label: '广告素材数', value: summary.adMaterialTotal, hint: '项目级和分集级广告素材' },
])

const stageCards = computed(() => [
  { key: 'planning', label: '策划中', value: summary.projectStageDistribution.planning, type: 'default' },
  { key: 'scripting', label: '剧本中', value: summary.projectStageDistribution.scripting, type: 'info' },
  { key: 'storyboard', label: '分镜中', value: summary.projectStageDistribution.storyboard, type: 'info' },
  { key: 'localization', label: '本地化中', value: summary.projectStageDistribution.localization, type: 'warning' },
  { key: 'material', label: '素材制作中', value: summary.projectStageDistribution.material, type: 'warning' },
  { key: 'launch', label: '投放中', value: summary.projectStageDistribution.launch, type: 'success' },
  { key: 'completed', label: '已完成', value: summary.projectStageDistribution.completed, type: 'success' },
])

const episodeStatusCards = computed(() => [
  { label: '分集总数', value: summary.episodeStatus.episodeTotal, type: 'default' },
  { label: '待分镜', value: summary.episodeStatus.pendingStoryboard, type: 'warning' },
  { label: '已完成分镜', value: summary.episodeStatus.completedStoryboard, type: 'info' },
  { label: '已完成本地化', value: summary.episodeStatus.completedLocalization, type: 'info' },
  { label: '已上传媒体', value: summary.episodeStatus.uploadedMedia, type: 'success' },
  { label: '已完成分集', value: summary.episodeStatus.completedEpisodes, type: 'success' },
])

const chainItems = [
  { key: 'project', title: 'Project 短剧项目', description: '承载整部短剧的题材、市场、语言、阶段和负责人。' },
  { key: 'episode', title: 'Episode 分集', description: '承载单集生产状态，是具体内容生产的推进单位。' },
  { key: 'storyboard', title: 'Storyboard AI分镜', description: '按集生成镜头拆解、画面提示词和角色一致性提示词。' },
  { key: 'localization', title: 'Localization 本地化', description: '按集生成目标语言表达和海外市场适配版本。' },
  { key: 'media', title: 'MediaAssets 媒体资产', description: '按项目和分集沉淀视频、图片、字幕等素材。' },
  { key: 'ads', title: 'AdMaterials 广告素材', description: '支持项目级投放素材，也支持单集爆点素材。' },
  { key: 'analytics', title: 'GrowthAnalytics 增长分析', description: '用 CTR、CVR、ROI 反向优化内容生产。' },
]

async function loadSummary() {
  const result = await request.get<unknown, ApiResponse<Partial<DashboardSummary>>>('/dashboard/summary')
  if (result.code === 0) {
    Object.assign(summary, {
      ...summary,
      ...result.data,
      projectStageDistribution: {
        ...summary.projectStageDistribution,
        ...(result.data.projectStageDistribution || {}),
      },
      episodeStatus: {
        ...summary.episodeStatus,
        ...(result.data.episodeStatus || {}),
      },
      recentProjects: result.data.recentProjects || [],
      recentEpisodes: result.data.recentEpisodes || [],
    })
  }
}

async function loadAiStatus() {
  const result = await getAiStatus()
  if (result.code === 0) aiStatus.value = result.data
}

function goProject(projectId: number) {
  router.push(`/projects/${projectId}`)
}

function goEpisodes(projectId: number) {
  router.push(`/projects/${projectId}/episodes`)
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function stageTagType(stage: ProjectStage) {
  if (stage === 'completed' || stage === 'launch') return 'success'
  if (stage === 'material' || stage === 'localization') return 'warning'
  if (stage === 'storyboard' || stage === 'scripting') return 'info'
  return 'default'
}

function episodeStageTagType(stage: EpisodeStage) {
  if (stage === 'completed') return 'success'
  if (stage === 'media' || stage === 'localization') return 'warning'
  if (stage === 'storyboard' || stage === 'scripting') return 'info'
  return 'default'
}

function subStatusText(status?: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status || 'pending'] || status || '待处理'
}

onMounted(async () => {
  loading.value = true
  errorText.value = ''
  try {
    await Promise.all([loadSummary(), loadAiStatus()])
  } catch {
    errorText.value = '首页看板加载失败，请确认后端服务已启动。'
    message.error(errorText.value)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.dashboard :deep(.n-spin-content) {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dashboard :deep(.n-card) {
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
}

.hero-card {
  background: linear-gradient(135deg, #f8fafc, #eef6ff);
}

.hero-content,
.ai-status {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow {
  margin-bottom: 6px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 800;
}

.hero-content h2 {
  margin: 0;
  color: #111827;
  font-size: 26px;
}

.hero-content p {
  max-width: 820px;
  margin: 10px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.metric-card {
  min-height: 132px;
}

.metric {
  color: #111827;
  font-size: 32px;
  font-weight: 900;
  line-height: 1.1;
}

.metric-label {
  margin-top: 8px;
  color: #111827;
  font-weight: 800;
}

.hint {
  margin-top: 8px;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.55;
}

.stage-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid #edf0f5;
  border-radius: 8px;
  background: #fbfcff;
}

.stage-item strong {
  color: #111827;
  font-size: 22px;
}

.list-card {
  min-height: 330px;
}

.list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #edf0f5;
}

.list-row:last-child {
  border-bottom: 0;
}

.clickable {
  cursor: pointer;
}

.clickable:hover .row-title {
  color: #18a058;
}

.row-main {
  min-width: 0;
}

.row-title {
  color: #111827;
  font-weight: 800;
  word-break: break-word;
}

.row-meta {
  margin-top: 5px;
  color: #6b7280;
  font-size: 12px;
}

.chain {
  display: grid;
  grid-template-columns: repeat(7, minmax(132px, 1fr));
  gap: 8px;
  overflow-x: auto;
}

.chain-item {
  min-width: 132px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}

.chain-title {
  color: #111827;
  font-weight: 900;
}

.chain-item p {
  margin: 6px 0 0;
  color: #4b5563;
  font-size: 12px;
  line-height: 1.5;
}

.chain-note {
  margin-top: 14px;
}

.status-title {
  color: #111827;
  font-size: 18px;
  font-weight: 800;
}

.status-copy {
  margin-top: 6px;
  color: #4b5563;
  line-height: 1.6;
}

@media (max-width: 960px) {
  .hero-content,
  .ai-status,
  .list-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .stage-grid {
    grid-template-columns: 1fr;
  }
}
</style>
