<template>
  <div class="list-page">
    <n-card :bordered="false" class="intro-card">
      <div class="intro-title">分镜任务列表</div>
      <div class="intro-copy">分镜结果会沉淀为可复用资产，后续可对接图片生成、视频生成和剪辑流程。</div>
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
            <n-form-item label="角色一致性状态">
              <n-select v-model:value="filters.consistency_status" clearable :options="consistencyOptions" placeholder="全部状态" />
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
            <n-empty v-if="!loading && !filteredRows.length" description="当前暂无分镜任务，生成后的分镜会沉淀到这里。" />
          </template>
        </n-data-table>
      </n-space>
    </n-card>

    <n-drawer v-model:show="detailVisible" width="720">
      <n-drawer-content title="分镜任务详情" closable>
        <n-space vertical size="large" v-if="currentRecord">
          <n-descriptions bordered :column="2" size="small">
            <n-descriptions-item label="标题">{{ currentRecord.title || '-' }}</n-descriptions-item>
            <n-descriptions-item label="分镜数量">{{ currentRecord.sceneCount || sceneCount(currentRecord) }}</n-descriptions-item>
            <n-descriptions-item label="分集 ID">{{ currentRecord.episode_id || '-' }}</n-descriptions-item>
            <n-descriptions-item label="集数">{{ currentRecord.episode_no ? `第 ${currentRecord.episode_no} 集` : '-' }}</n-descriptions-item>
            <n-descriptions-item label="风格">{{ currentRecord.style || '-' }}</n-descriptions-item>
            <n-descriptions-item label="生成时间">{{ formatTime(currentRecord.createdAt) }}</n-descriptions-item>
          </n-descriptions>
          <pre class="json-box">{{ JSON.stringify(currentRecord.result, null, 2) }}</pre>
        </n-space>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { getProjects } from '../api/projects'
import { getStoryboardHistory } from '../api/storyboard'
import { useDictionaries } from "../composables/useDictionaries";
import type { StoryboardHistoryItem, StoryboardScene, StoryboardSceneText } from '../types/storyboard'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const { getLabel } = useDictionaries()
const loading = ref(false)
const rows = ref<StoryboardHistoryItem[]>([])
const projectOptions = ref<{ label: string; value: number }[]>([])
const projectNameMap = ref<Record<number, string>>({})
const detailVisible = ref(false)
const currentRecord = ref<StoryboardHistoryItem | null>(null)

const filters = reactive({
  project_id: null as number | null,
  episode_id: null as number | null,
  episode_no: null as number | null,
  target_language: '',
  consistency_status: null as string | null,
})

const consistencyOptions = [
  { label: '已包含一致性提示词', value: 'ready' },
  { label: '缺少一致性提示词', value: 'missing' },
]

function getSceneText(scene: StoryboardScene): StoryboardSceneText & { language?: string } {
  const target = scene.bilingual?.target
  const zh = scene.bilingual?.zh
  const source = typeof target === 'object' && target ? target : typeof zh === 'object' && zh ? zh : scene
  return source
}

function sceneCount(row: StoryboardHistoryItem) {
  return row.result?.scenes?.length || row.sceneCount || 0
}

function hasConsistency(row: StoryboardHistoryItem) {
  return Boolean(row.result?.scenes?.some((scene) => getSceneText(scene).consistencyPrompt || scene.consistencyPrompt))
}

function targetLanguage(row: StoryboardHistoryItem) {
  const target = row.result?.scenes?.find((scene) => typeof scene.bilingual?.target === 'object')?.bilingual?.target
  return typeof target === 'object' ? getLabel('languages', target.language) || '-' : '-'
}

const filteredRows = computed(() => {
  return rows.value.filter((row) => {
    if (filters.target_language && !targetLanguage(row).includes(filters.target_language)) return false
    if (filters.consistency_status === 'ready' && !hasConsistency(row)) return false
    if (filters.consistency_status === 'missing' && hasConsistency(row)) return false
    return true
  })
})

const columns: DataTableColumns<StoryboardHistoryItem> = [
  { title: '所属项目', key: 'project_id', minWidth: 160, render: (row) => row.project_id ? projectNameMap.value[row.project_id] || `项目 ${row.project_id}` : '-' },
  { title: '集数', key: 'episode_no', width: 90, render: (row) => row.episode_no ? `第 ${row.episode_no} 集` : '-' },
  { title: '分集 ID', key: 'episode_id', width: 90, render: (row) => row.episode_id || '-' },
  { title: '剧集编号 / 分镜标题', key: 'title', minWidth: 180, render: (row) => row.result?.storyboardTitle || row.title || '-' },
  { title: '分镜数量', key: 'sceneCount', width: 100, render: (row) => sceneCount(row) },
  { title: '目标语言', key: 'language', width: 150, render: (row) => targetLanguage(row) },
  {
    title: '角色一致性状态',
    key: 'consistency',
    width: 150,
    render: (row) => h(NTag, { type: hasConsistency(row) ? 'success' : 'warning', bordered: false }, { default: () => hasConsistency(row) ? '已包含' : '待补充' }),
  },
  { title: '生成时间', key: 'createdAt', width: 170, render: (row) => formatTime(row.createdAt) },
  {
    title: '操作',
    key: 'actions',
    width: 360,
    render: (row) => h(NSpace, { size: 8 }, {
      default: () => [
        h(NButton, { size: 'small', secondary: true, onClick: () => showDetail(row) }, { default: () => '查看详情' }),
        h(NButton, { size: 'small', secondary: true, onClick: () => exportJson(row) }, { default: () => '导出 JSON' }),
        h(NButton, { size: 'small', tertiary: true, onClick: () => copyPrompts(row) }, { default: () => '复制 Prompt' }),
      ],
    }),
  },
]

function formatTime(value?: string) {
  return value ? new Date(value).toLocaleString() : '-'
}

function showDetail(row: StoryboardHistoryItem) {
  currentRecord.value = row
  detailVisible.value = true
}

function exportJson(row: StoryboardHistoryItem) {
  const blob = new Blob([JSON.stringify(row.result || row, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `storyboard-${row.id}.json`
  link.click()
  URL.revokeObjectURL(url)
}

async function copyPrompts(row: StoryboardHistoryItem) {
  const prompts = (row.result?.scenes || [])
    .map((scene, index) => {
      const text = getSceneText(scene)
      return [`#${index + 1}`, text.visualPrompt || scene.visualPrompt || '', text.motionPrompt || scene.motionPrompt || '', text.consistencyPrompt || scene.consistencyPrompt || ''].filter(Boolean).join('\n')
    })
    .filter(Boolean)
    .join('\n\n')
  if (!prompts) {
    message.warning('当前分镜暂无可复制的 Prompt')
    return
  }
  await navigator.clipboard.writeText(prompts)
  message.success('Prompt 已复制')
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
    const response = await getStoryboardHistory({
      project_id: filters.project_id || undefined,
      episode_id: filters.episode_id || undefined,
      episode_no: filters.episode_no || undefined,
    })
    if (response.code === 0) rows.value = response.data
  } catch {
    message.error('分镜任务加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

async function resetFilters() {
  filters.project_id = null
  filters.episode_id = null
  filters.episode_no = null
  filters.target_language = ''
  filters.consistency_status = null
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

.json-box {
  max-height: 680px;
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
