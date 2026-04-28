<template>
  <div class="list-page">
    <n-card :bordered="false" class="intro-card">
      <div class="intro-title">广告素材库</div>
      <div class="intro-copy">广告素材生成后进入素材库，并结合 CTR、CVR、ROI 做投放复盘。</div>
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
            <n-form-item label="目标市场">
              <n-select v-model:value="filters.market" clearable :options="marketOptions" placeholder="全部市场" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="4" :s-span="24">
            <n-form-item label="素材类型">
              <n-input v-model:value="filters.material_type" placeholder="如 情感反转" />
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
            <n-empty v-if="!loading && !filteredRows.length" description="当前暂无广告素材，生成后的素材会沉淀到这里。" />
          </template>
        </n-data-table>
      </n-space>
    </n-card>

    <n-modal v-model:show="detailVisible" preset="card" title="广告素材详情" class="detail-modal">
      <n-space vertical size="large" v-if="currentRecord">
        <n-descriptions bordered :column="2" size="small">
          <n-descriptions-item label="分集 ID">{{ currentRecord.episode_id || '-' }}</n-descriptions-item>
          <n-descriptions-item label="集数">{{ currentRecord.episode_no ? `第 ${currentRecord.episode_no} 集` : '-' }}</n-descriptions-item>
        </n-descriptions>
        <n-card size="small" title="标题">
          <n-space><n-tag v-for="item in titles(currentRecord)" :key="item" type="info" bordered>{{ item }}</n-tag></n-space>
        </n-card>
        <n-card size="small" title="前三秒 Hook">
          <n-list><n-list-item v-for="item in hooks(currentRecord)" :key="item">{{ item }}</n-list-item></n-list>
        </n-card>
        <n-card size="small" title="正文 / CTA / 封面提示词">
          <pre class="json-box">{{ JSON.stringify(currentRecord.result, null, 2) }}</pre>
        </n-card>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { getAdMaterialHistory } from '../api/ads'
import { getProjects } from '../api/projects'
import type { AdMaterialHistoryItem } from '../types/ads'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const rows = ref<AdMaterialHistoryItem[]>([])
const projectOptions = ref<{ label: string; value: number }[]>([])
const projectNameMap = ref<Record<number, string>>({})
const detailVisible = ref(false)
const currentRecord = ref<AdMaterialHistoryItem | null>(null)

const filters = reactive({
  project_id: null as number | null,
  episode_id: null as number | null,
  episode_no: null as number | null,
  market: null as string | null,
  material_type: '',
})

const marketOptions = ['北美', '东南亚', '日本', '韩国', '中东', '中国大陆'].map((item) => ({ label: item, value: item }))

const filteredRows = computed(() => rows.value.filter((row) => {
  if (filters.market && row.market !== filters.market) return false
  if (filters.material_type && !row.contentType.includes(filters.material_type)) return false
  return true
}))

const columns: DataTableColumns<AdMaterialHistoryItem> = [
  { title: '所属项目', key: 'project_id', minWidth: 160, render: (row) => row.project_id ? projectNameMap.value[row.project_id] || `项目 ${row.project_id}` : '-' },
  { title: '集数', key: 'episode_no', width: 90, render: (row) => row.episode_no ? `第 ${row.episode_no} 集` : '-' },
  { title: '分集 ID', key: 'episode_id', width: 90, render: (row) => row.episode_id || '-' },
  { title: '目标市场', key: 'market', width: 100 },
  { title: '素材类型', key: 'contentType', width: 130 },
  { title: '标题数量', key: 'titles', width: 100, render: (row) => titles(row).length },
  { title: 'Hook 数量', key: 'hooks', width: 100, render: (row) => hooks(row).length },
  { title: 'CTA 数量', key: 'cta', width: 100, render: (row) => row.result?.cta?.length || 0 },
  { title: 'CTR', key: 'ctr', width: 80, render: (row) => `${mockMetric(row.id, 2.4, 7.8)}%` },
  { title: 'CVR', key: 'cvr', width: 80, render: (row) => `${mockMetric(row.id + 3, 1.1, 4.2)}%` },
  { title: 'ROI', key: 'roi', width: 80, render: (row) => mockMetric(row.id + 7, 1.2, 3.8) },
  { title: '生成时间', key: 'createdAt', width: 170, render: (row) => formatTime(row.createdAt) },
  {
    title: '操作',
    key: 'actions',
    width: 300,
    render: (row) => h(NSpace, { size: 8 }, {
      default: () => [
        h(NButton, { size: 'small', secondary: true, onClick: () => showDetail(row) }, { default: () => '查看详情' }),
        h(NButton, { size: 'small', secondary: true, onClick: () => copyMaterial(row) }, { default: () => '复制素材' }),
        h(NButton, { size: 'small', tertiary: true, onClick: () => router.push(`/growth-analytics${row.project_id ? `?projectId=${row.project_id}` : ''}`) }, { default: () => '增长分析' }),
        h(NButton, { size: 'small', tertiary: true, disabled: !row.project_id, onClick: () => row.project_id && router.push(`/projects/${row.project_id}`) }, { default: () => '项目详情' }),
      ],
    }),
  },
]

function titles(row: AdMaterialHistoryItem) {
  return row.result?.titles || []
}

function hooks(row: AdMaterialHistoryItem) {
  return row.result?.hooks || []
}

function mockMetric(seed: number, min: number, max: number) {
  return (min + (seed % 10) / 10 * (max - min)).toFixed(1)
}

function formatTime(value?: string) {
  return value ? new Date(value).toLocaleString() : '-'
}

function showDetail(row: AdMaterialHistoryItem) {
  currentRecord.value = row
  detailVisible.value = true
}

async function copyMaterial(row: AdMaterialHistoryItem) {
  const parts = [
    ...titles(row),
    ...hooks(row),
    ...(row.result?.copies || []).map((item) => typeof item === 'string' ? item : item.copy),
    ...(row.result?.cta || []),
    row.result?.coverPrompt || '',
  ].filter(Boolean)
  if (!parts.length) {
    message.warning('当前记录暂无可复制素材')
    return
  }
  await navigator.clipboard.writeText(parts.join('\n'))
  message.success('广告素材已复制')
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
    const response = await getAdMaterialHistory({
      project_id: filters.project_id || undefined,
      episode_id: filters.episode_id || undefined,
      episode_no: filters.episode_no || undefined,
    })
    if (response.code === 0) rows.value = response.data
  } catch {
    message.error('广告素材库加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

async function resetFilters() {
  filters.project_id = null
  filters.episode_id = null
  filters.episode_no = null
  filters.market = null
  filters.material_type = ''
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
  width: min(900px, 92vw);
}

.json-box {
  max-height: 420px;
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
