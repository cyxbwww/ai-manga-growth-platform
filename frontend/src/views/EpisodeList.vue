<template>
  <div class="episode-page">
    <n-card bordered class="intro-card">
      <div class="intro-header">
        <div>
          <h2>分集管理</h2>
          <p>
            {{ projectName ? `${projectName} / ` : '' }}分集用于承载单集剧本、分镜、本地化和媒体资产，是短剧生产的最小推进单元。
          </p>
        </div>
        <n-space>
          <n-button secondary @click="router.push(`/projects/${projectId}`)">返回项目详情</n-button>
          <n-button type="primary" @click="openCreateModal">新增分集</n-button>
        </n-space>
      </div>
    </n-card>

    <n-card title="分集列表" bordered class="table-card">
      <template #header-extra>
        <n-button size="small" secondary :loading="batchLoading" @click="handleBatchGenerate">批量生成分集</n-button>
      </template>

      <div class="filter-bar">
        <n-input v-model:value="filters.keyword" clearable placeholder="搜索分集标题或摘要" />
        <n-select v-model:value="filters.stage" clearable placeholder="当前阶段" :options="stageOptions" />
        <n-select v-model:value="filters.status" clearable placeholder="分集状态" :options="statusOptions" />
        <n-button type="primary" @click="loadEpisodes">查询</n-button>
        <n-button secondary @click="resetFilters">重置</n-button>
      </div>

      <n-data-table
        :columns="columns"
        :data="episodes"
        :loading="loading"
        :bordered="false"
        :single-line="false"
        :pagination="false"
      >
        <template #empty>
          <n-empty description="当前项目暂无分集，可新增分集或批量生成分集骨架。" />
        </template>
      </n-data-table>

      <div class="table-footer">
        <span>共 {{ total }} 集</span>
      </div>
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑分集大纲' : '新增分集'" class="episode-modal" :style="{ width: '70%' }">
      <n-form :model="form" label-placement="top">
        <n-alert v-if="editingId" type="info" :bordered="false" class="outline-edit-tip">
          AI 生成的分集大纲为初稿，可在这里逐集调整后再进入剧本打磨、AI分镜和本地化生产。
        </n-alert>
        <n-grid :cols="2" :x-gap="16">
          <n-form-item-gi label="集数">
            <n-input-number v-model:value="form.episode_no" :min="1" :max="500" class="full-width" />
          </n-form-item-gi>
          <n-form-item-gi label="分集标题">
            <n-input v-model:value="form.title" placeholder="请输入分集标题" />
          </n-form-item-gi>
          <n-form-item-gi label="当前阶段">
            <n-select v-model:value="form.stage" :options="stageOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="分集状态">
            <n-select v-model:value="form.status" :options="statusOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="剧本状态">
            <n-select v-model:value="form.script_status" :options="subStatusOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="分镜状态">
            <n-select v-model:value="form.storyboard_status" :options="subStatusOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="本地化状态">
            <n-select v-model:value="form.localization_status" :options="subStatusOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="媒体状态">
            <n-select v-model:value="form.media_status" :options="subStatusOptions" />
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="剧情摘要">
          <n-input v-model:value="form.summary" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" placeholder="可包含本集剧情推进、核心冲突、开场钩子和结尾悬念。" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button secondary @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitEpisode">{{ editingId ? '保存修改' : '创建分集' }}</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NPopconfirm, NSpace, NTag, useMessage } from 'naive-ui'
import { getProjectDetail } from '../api/projects'
import {
  archiveEpisode,
  batchGenerateEpisodes,
  createProjectEpisode,
  getProjectEpisodes,
  updateEpisode,
} from '../api/episodes'
import type {
  ShortDramaEpisode,
  ShortDramaEpisodeCreate,
  ShortDramaEpisodeStage,
  ShortDramaEpisodeStatus,
  ShortDramaEpisodeSubStatus,
  ShortDramaEpisodeUpdate,
} from '../types/episode'

type EpisodeForm = ShortDramaEpisodeCreate & {
  script_status: ShortDramaEpisodeSubStatus
  storyboard_status: ShortDramaEpisodeSubStatus
  localization_status: ShortDramaEpisodeSubStatus
  media_status: ShortDramaEpisodeSubStatus
}

const route = useRoute()
const router = useRouter()
const message = useMessage()

const loading = ref(false)
const saving = ref(false)
const batchLoading = ref(false)
const showModal = ref(false)
const editingId = ref<number | null>(null)
const episodes = ref<ShortDramaEpisode[]>([])
const total = ref(0)
const projectName = ref('')

const projectId = computed(() => String(route.params.id || ''))

const filters = reactive({
  keyword: '',
  stage: undefined as ShortDramaEpisodeStage | undefined,
  status: undefined as ShortDramaEpisodeStatus | undefined,
})

const defaultForm: EpisodeForm = {
  project_id: 0,
  episode_no: 1,
  title: '',
  summary: '',
  stage: 'planning',
  status: 'active',
  script_status: 'pending',
  storyboard_status: 'pending',
  localization_status: 'pending',
  media_status: 'pending',
}

const form = reactive<EpisodeForm>({ ...defaultForm })

const stageMap: Record<ShortDramaEpisodeStage, string> = {
  planning: '策划中',
  scripting: '剧本中',
  storyboard: '分镜中',
  localization: '本地化中',
  media: '媒体制作中',
  completed: '已完成',
}

const statusMap: Record<ShortDramaEpisodeStatus, string> = {
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
  archived: '已归档',
}

const subStatusMap: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
}

const stageOptions = Object.entries(stageMap).map(([value, label]) => ({ value, label }))
const statusOptions = Object.entries(statusMap).map(([value, label]) => ({ value, label }))
const subStatusOptions = Object.entries(subStatusMap).map(([value, label]) => ({ value, label }))

function stageTagType(stage: ShortDramaEpisodeStage) {
  if (stage === 'completed') return 'success'
  if (stage === 'media' || stage === 'localization') return 'warning'
  return 'info'
}

function statusTagType(status: ShortDramaEpisodeStatus) {
  if (status === 'active') return 'success'
  if (status === 'archived') return 'default'
  if (status === 'paused') return 'warning'
  return 'info'
}

function subStatusTagType(status?: ShortDramaEpisodeSubStatus | null) {
  if (status === 'completed') return 'success'
  if (status === 'processing') return 'warning'
  if (status === 'failed') return 'error'
  return 'default'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function resetForm() {
  Object.assign(form, {
    ...defaultForm,
    project_id: Number(projectId.value),
    episode_no: episodes.value.length + 1,
  })
}

function openCreateModal() {
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEditModal(row: ShortDramaEpisode) {
  editingId.value = row.id
  Object.assign(form, {
    project_id: row.project_id,
    episode_no: row.episode_no,
    title: row.title,
    summary: row.summary || '',
    stage: row.stage,
    status: row.status,
    script_status: row.script_status || 'pending',
    storyboard_status: row.storyboard_status || 'pending',
    localization_status: row.localization_status || 'pending',
    media_status: row.media_status || 'pending',
  })
  showModal.value = true
}

function goProduction(path: string, row: ShortDramaEpisode) {
  // 当前生成页先透传 episodeId / episodeNo，后续第 6 步可在生成接口中正式绑定 episode_id。
  router.push(`${path}?projectId=${projectId.value}&episodeId=${row.id}&episodeNo=${row.episode_no}`)
}

function assetCount(value?: number) {
  return value ?? 0
}

function goAssetList(path: string, row: ShortDramaEpisode) {
  // 资产沉淀标签直接跳转到对应资产列表，并携带 projectId + episodeId + episodeNo 完成单集筛选。
  router.push(`${path}?projectId=${projectId.value}&episodeId=${row.id}&episodeNo=${row.episode_no}`)
}

const columns: DataTableColumns<ShortDramaEpisode> = [
  { title: '集数', key: 'episode_no', width: 80, render: (row) => `第 ${row.episode_no} 集` },
  {
    title: '分集标题',
    key: 'title',
    minWidth: 180,
    render(row) {
      return h('div', { class: 'title-cell' }, [
        h('div', { class: 'episode-title' }, row.title),
        h('div', { class: 'episode-summary' }, row.summary || '暂无剧情摘要'),
      ])
    },
  },
  {
    title: '当前阶段',
    key: 'stage',
    width: 110,
    render(row) {
      return h(NTag, { type: stageTagType(row.stage), bordered: false }, { default: () => stageMap[row.stage] || row.stage })
    },
  },
  {
    title: '剧本状态',
    key: 'script_status',
    width: 110,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.script_status), bordered: false }, { default: () => subStatusMap[row.script_status || 'pending'] || row.script_status || '-' })
    },
  },
  {
    title: '分镜状态',
    key: 'storyboard_status',
    width: 110,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.storyboard_status), bordered: false }, { default: () => subStatusMap[row.storyboard_status || 'pending'] || row.storyboard_status || '-' })
    },
  },
  {
    title: '本地化状态',
    key: 'localization_status',
    width: 120,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.localization_status), bordered: false }, { default: () => subStatusMap[row.localization_status || 'pending'] || row.localization_status || '-' })
    },
  },
  {
    title: '媒体状态',
    key: 'media_status',
    width: 110,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.media_status), bordered: false }, { default: () => subStatusMap[row.media_status || 'pending'] || row.media_status || '-' })
    },
  },
  {
    title: '资产沉淀',
    key: 'asset_counts',
    width: 260,
    render(row) {
      return h(NSpace, { size: 6, wrap: true }, {
        default: () => [
          h(NTag, { type: 'info', bordered: false, class: 'asset-tag', onClick: () => goAssetList('/storyboards', row) }, { default: () => `分镜 ${assetCount(row.storyboard_count)}` }),
          h(NTag, { type: 'success', bordered: false, class: 'asset-tag', onClick: () => goAssetList('/localizations', row) }, { default: () => `本地化 ${assetCount(row.localization_count)}` }),
          h(NTag, { type: 'warning', bordered: false, class: 'asset-tag', onClick: () => goAssetList('/media-assets', row) }, { default: () => `媒体 ${assetCount(row.media_asset_count)}` }),
          h(NTag, { type: 'error', bordered: false, class: 'asset-tag', onClick: () => goAssetList('/ad-materials/list', row) }, { default: () => `广告 ${assetCount(row.ad_material_count)}` }),
        ],
      })
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 170,
    render(row) {
      return formatTime(row.updated_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 700,
    fixed: 'right',
    render(row) {
      return h(NSpace, { size: 6, wrap: true }, {
        default: () => [
          h(NButton, { size: 'small', secondary: true, onClick: () => openEditModal(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'primary', secondary: true, onClick: () => goProduction('/script-polish', row) }, { default: () => '进入剧本打磨' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/storyboard', row) }, { default: () => '进入分镜制作' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/storyboards', row) }, { default: () => '查看分镜任务' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/localization', row) }, { default: () => '进入本地化' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/localizations', row) }, { default: () => '查看本地化版本' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/media-assets', row) }, { default: () => '上传媒体' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/ad-materials', row) }, { default: () => '生成广告素材' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => goProduction('/ad-materials/list', row) }, { default: () => '查看广告素材' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleArchive(row.id) },
            {
              trigger: () => h(NButton, { size: 'small', type: 'error', secondary: true }, { default: () => '归档' }),
              default: () => '确认归档该分集？',
            },
          ),
        ],
      })
    },
  },
]

async function loadProject() {
  try {
    const res = await getProjectDetail(Number(projectId.value))
    if (res.code === 0) {
      projectName.value = res.data.name
    }
  } catch {
    message.error('项目不存在或加载失败')
    router.push('/projects')
  }
}

async function loadEpisodes() {
  loading.value = true
  try {
    const res = await getProjectEpisodes(projectId.value, {
      keyword: filters.keyword || undefined,
      stage: filters.stage || undefined,
      status: filters.status || undefined,
      limit: 200,
    })
    if (res.code === 0) {
      episodes.value = res.data.items
      total.value = res.data.total
    }
  } catch {
    message.error('分集列表加载失败')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.stage = undefined
  filters.status = undefined
  loadEpisodes()
}

async function submitEpisode() {
  if (!form.title.trim()) {
    message.warning('请输入分集标题')
    return
  }
  if (!form.episode_no) {
    message.warning('请输入集数')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      const data: ShortDramaEpisodeUpdate = {
        episode_no: form.episode_no,
        title: form.title,
        summary: form.summary,
        stage: form.stage,
        status: form.status,
        script_status: form.script_status,
        storyboard_status: form.storyboard_status,
        localization_status: form.localization_status,
        media_status: form.media_status,
      }
      await updateEpisode(editingId.value, data)
      message.success('分集已更新')
    } else {
      await createProjectEpisode(projectId.value, {
        project_id: Number(projectId.value),
        episode_no: form.episode_no,
        title: form.title,
        summary: form.summary,
        stage: form.stage,
        status: form.status,
      })
      message.success('分集已创建')
    }
    showModal.value = false
    await loadEpisodes()
  } catch (error: any) {
    message.error(error?.response?.data?.detail || '保存分集失败')
  } finally {
    saving.value = false
  }
}

async function handleArchive(id: number) {
  try {
    await archiveEpisode(id)
    message.success('分集已归档')
    await loadEpisodes()
  } catch {
    message.error('归档分集失败')
  }
}

async function handleBatchGenerate() {
  batchLoading.value = true
  try {
    const res = await batchGenerateEpisodes(projectId.value)
    message.success(res.message || '分集骨架已生成')
    await loadEpisodes()
  } catch {
    message.error('批量生成分集失败')
  } finally {
    batchLoading.value = false
  }
}

onMounted(async () => {
  await loadProject()
  await loadEpisodes()
})
</script>

<style scoped>
.episode-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.episode-page :deep(.n-card) {
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
}

.intro-card {
  background: linear-gradient(135deg, #f8fafc, #eef6ff);
}

.intro-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.intro-header h2 {
  margin: 0;
  color: #111827;
  font-size: 24px;
}

.intro-header p {
  max-width: 820px;
  margin: 10px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.filter-bar {
  display: grid;
  grid-template-columns: minmax(240px, 1.5fr) minmax(160px, 1fr) minmax(160px, 1fr) auto auto;
  gap: 12px;
  margin-bottom: 16px;
}

.table-footer {
  margin-top: 14px;
  color: #6b7280;
  font-size: 13px;
}

.title-cell {
  min-width: 0;
}

.episode-title {
  color: #111827;
  font-weight: 700;
}

.episode-summary {
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.outline-edit-tip {
  margin-bottom: 14px;
}

.episode-page :deep(.asset-tag) {
  cursor: pointer;
  padding: 0 7px;
  margin-right: 2px;
}

.episode-page :deep(.asset-tag:hover) {
  opacity: 0.86;
}

.full-width {
  width: 100%;
}

.episode-modal {
  width: min(760px, 92vw);
}

@media (max-width: 960px) {
  .intro-header {
    flex-direction: column;
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
