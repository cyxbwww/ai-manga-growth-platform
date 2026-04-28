<template>
  <div class="list-page">
    <n-card :bordered="false" class="intro-card">
      <div class="intro-title">本地化版本列表</div>
      <div class="intro-copy">本地化结果会按短剧项目和目标市场沉淀，方便海外发行团队审核和复用。</div>
    </n-card>

    <n-card :bordered="false">
      <n-space vertical size="large">
        <n-grid :cols="24" :x-gap="14" :y-gap="14" responsive="screen">
          <n-grid-item :span="8" :s-span="24">
            <n-form-item label="短剧项目">
              <n-select v-model:value="filters.project_id" clearable filterable :options="projectOptions" placeholder="全部项目" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="5" :s-span="24">
            <n-form-item label="集数">
              <n-input-number v-model:value="filters.episode_no" clearable :min="1" placeholder="全部集数" class="full-width" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="4" :s-span="24">
            <n-form-item label="目标语言">
              <n-input v-model:value="filters.target_language" placeholder="如 英语 / 日语" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="4" :s-span="24">
            <n-form-item label="状态">
              <n-select v-model:value="filters.status" clearable :options="statusOptions" placeholder="全部状态" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="3" :s-span="24">
            <n-form-item label="操作">
              <n-space>
                <n-button type="primary" :loading="loading" @click="loadData">查询</n-button>
                <n-button @click="resetFilters">重置</n-button>
                <n-button v-if="filters.project_id && filters.episode_id" secondary @click="router.push(`/projects/${filters.project_id}/episodes`)">返回分集列表</n-button>
              </n-space>
            </n-form-item>
          </n-grid-item>
        </n-grid>

        <n-data-table :columns="columns" :data="filteredRows" :loading="loading" :bordered="false" :single-line="false">
          <template #empty>
            <n-empty v-if="!loading && !filteredRows.length" description="当前暂无本地化版本，生成后的本地化结果会沉淀到这里。" />
          </template>
        </n-data-table>
      </n-space>
    </n-card>

    <n-modal v-model:show="detailVisible" preset="card" title="本地化详情" class="detail-modal">
      <n-descriptions v-if="currentRecord" bordered :column="2" size="small" class="detail-desc">
        <n-descriptions-item label="分集 ID">{{ currentRecord.episode_id || '-' }}</n-descriptions-item>
        <n-descriptions-item label="集数">{{ currentRecord.episode_no ? `第 ${currentRecord.episode_no} 集` : '-' }}</n-descriptions-item>
      </n-descriptions>
      <pre v-if="currentRecord" class="json-box">{{ JSON.stringify(currentRecord.result, null, 2) }}</pre>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { getLocalizationHistory } from '../api/localization'
import { getProjects } from '../api/projects'
import type { LocalizationHistoryItem } from '../types/localization'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const rows = ref<LocalizationHistoryItem[]>([])
const projectOptions = ref<{ label: string; value: number }[]>([])
const projectNameMap = ref<Record<number, string>>({})
const detailVisible = ref(false)
const currentRecord = ref<LocalizationHistoryItem | null>(null)

const filters = reactive({
  project_id: null as number | null,
  episode_id: null as number | null,
  episode_no: null as number | null,
  target_language: '',
  status: null as string | null,
})

const statusOptions = [
  { label: '已完成', value: 'completed' },
  { label: '待处理', value: 'pending' },
]

function firstSubtitle(row: LocalizationHistoryItem) {
  return row.result?.subtitles?.[0]
}

function statusOf(row: LocalizationHistoryItem) {
  return firstSubtitle(row)?.subtitleStatus || '-'
}

function summary(text?: string) {
  if (!text) return '-'
  return text.length > 44 ? `${text.slice(0, 44)}...` : text
}

const filteredRows = computed(() => rows.value.filter((row) => {
  if (filters.target_language && !row.language.includes(filters.target_language)) return false
  if (filters.status === 'completed' && !statusOf(row).includes('完成')) return false
  if (filters.status === 'pending' && statusOf(row).includes('完成')) return false
  return true
}))

const columns: DataTableColumns<LocalizationHistoryItem> = [
  { title: '所属项目', key: 'project_id', minWidth: 160, render: (row) => row.project_id ? projectNameMap.value[row.project_id] || `项目 ${row.project_id}` : '-' },
  { title: '集数', key: 'episode_no', width: 90, render: (row) => row.episode_no ? `第 ${row.episode_no} 集` : '-' },
  { title: '分集 ID', key: 'episode_id', width: 90, render: (row) => row.episode_id || '-' },
  { title: '目标语言', key: 'language', width: 110 },
  { title: '本地化类型', key: 'strategy', width: 130 },
  { title: '中文审核稿摘要', key: 'originalText', minWidth: 180, render: (row) => summary(firstSubtitle(row)?.originalText) },
  { title: '目标语言稿摘要', key: 'localizedText', minWidth: 220, render: (row) => summary(firstSubtitle(row)?.localizedText) },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => h(NTag, { type: statusOf(row).includes('完成') ? 'success' : 'warning', bordered: false }, { default: () => statusOf(row) }),
  },
  { title: '生成时间', key: 'createdAt', width: 170, render: (row) => formatTime(row.createdAt) },
  {
    title: '操作',
    key: 'actions',
    width: 260,
    render: (row) => h(NSpace, { size: 8 }, {
      default: () => [
        h(NButton, { size: 'small', secondary: true, onClick: () => showDetail(row) }, { default: () => '查看详情' }),
        h(NButton, { size: 'small', secondary: true, onClick: () => copyTargetText(row) }, { default: () => '复制目标语言稿' }),
        h(NButton, { size: 'small', tertiary: true, disabled: !row.project_id, onClick: () => row.project_id && router.push(`/projects/${row.project_id}`) }, { default: () => '返回项目详情' }),
      ],
    }),
  },
]

function formatTime(value?: string) {
  return value ? new Date(value).toLocaleString() : '-'
}

function showDetail(row: LocalizationHistoryItem) {
  currentRecord.value = row
  detailVisible.value = true
}

async function copyTargetText(row: LocalizationHistoryItem) {
  const text = (row.result?.subtitles || []).map((item) => item.localizedText).filter(Boolean).join('\n')
  if (!text) {
    message.warning('当前记录暂无目标语言稿')
    return
  }
  await navigator.clipboard.writeText(text)
  message.success('目标语言稿已复制')
}

async function loadProjects() {
  const response = await getProjects({ limit: 100 })
  if (response.code !== 0) return
  projectOptions.value = response.data.items.map((item) => ({ label: `${item.name} / ${item.target_market}`, value: item.id }))
  projectNameMap.value = Object.fromEntries(response.data.items.map((item) => [item.id, item.name]))
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) filters.project_id = queryProjectId
  const queryEpisodeId = Number(route.query.episodeId)
  const queryEpisodeNo = Number(route.query.episodeNo)
  if (queryEpisodeId) filters.episode_id = queryEpisodeId
  if (queryEpisodeNo) filters.episode_no = queryEpisodeNo
}

async function loadData() {
  loading.value = true
  try {
    const response = await getLocalizationHistory({
      project_id: filters.project_id || undefined,
      episode_id: filters.episode_id || undefined,
      episode_no: filters.episode_no || undefined,
    })
    if (response.code === 0) rows.value = response.data
  } catch {
    message.error('本地化版本加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

async function resetFilters() {
  filters.project_id = null
  filters.episode_id = null
  filters.episode_no = null
  filters.target_language = ''
  filters.status = null
  await loadData()
}

onMounted(async () => {
  await loadProjects()
  await loadData()
})
</script>

<style scoped>
.list-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.intro-card {
  background: #fbfcff;
}

.intro-title {
  color: #111827;
  font-size: 22px;
  font-weight: 800;
}

.intro-copy {
  margin-top: 6px;
  color: #6b7280;
  line-height: 1.6;
}

.detail-modal {
  width: min(860px, 92vw);
}

.detail-desc {
  margin-bottom: 12px;
}

.json-box {
  max-height: 620px;
  padding: 14px;
  overflow: auto;
  border-radius: 8px;
  background: #f7f8fa;
  white-space: pre-wrap;
  word-break: break-word;
}

.full-width {
  width: 100%;
}
</style>
