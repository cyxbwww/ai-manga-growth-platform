<template>
  <div class="episode-picker">
    <div class="picker-card" :class="{ disabled: disabled || !projectId }">
      <div class="picker-main">
        <template v-if="selectedEpisode">
          <div class="episode-title">第 {{ selectedEpisode.episode_no }} 集：{{ selectedEpisode.title }}</div>
          <n-space size="small" class="episode-tags">
            <n-tag :type="stageTagType(selectedEpisode.stage)" size="small" :bordered="false">{{ stageMap[selectedEpisode.stage] }}</n-tag>
            <n-tag :type="subStatusTagType(selectedEpisode.storyboard_status)" size="small" :bordered="false">分镜 {{ subStatusLabel(selectedEpisode.storyboard_status) }}</n-tag>
            <n-tag :type="subStatusTagType(selectedEpisode.localization_status)" size="small" :bordered="false">本地化 {{ subStatusLabel(selectedEpisode.localization_status) }}</n-tag>
            <n-tag :type="subStatusTagType(selectedEpisode.media_status)" size="small" :bordered="false">媒体 {{ subStatusLabel(selectedEpisode.media_status) }}</n-tag>
          </n-space>
        </template>
        <template v-else>
          <div class="episode-title muted">{{ projectId ? placeholder : '请先选择短剧项目' }}</div>
          <div class="episode-meta">选择具体分集后，分镜、本地化和媒体资产会沉淀到对应 Episode。</div>
        </template>
      </div>
      <n-space class="picker-actions" size="small">
        <n-button size="small" secondary :disabled="disabled || !projectId" @click="openModal">{{ selectedEpisode ? '重新选择' : '选择分集' }}</n-button>
        <n-button v-if="clearable && selectedEpisode" size="small" quaternary :disabled="disabled" @click="clearEpisode">清空</n-button>
      </n-space>
    </div>

    <n-modal v-model:show="showModal" preset="card" title="选择短剧分集" class="episode-picker-modal" :style="{ width: '900px' }">
      <!-- EpisodePicker 用于分集级生产页选择具体集数，避免生成结果无法归属到具体 Episode。 -->
      <n-space vertical size="medium">
        <n-card size="small" :bordered="false" class="filter-card">
          <n-grid :cols="24" :x-gap="12" :y-gap="12" responsive="screen">
            <n-grid-item :span="8" :s-span="24">
              <n-input v-model:value="filters.keyword" clearable placeholder="分集标题 / 摘要" @keyup.enter="loadEpisodes" />
            </n-grid-item>
            <n-grid-item :span="6" :s-span="12">
              <n-select v-model:value="filters.stage" clearable placeholder="阶段" :options="stageOptions" />
            </n-grid-item>
            <n-grid-item :span="6" :s-span="12">
              <n-select v-model:value="filters.status" clearable placeholder="状态" :options="statusOptions" />
            </n-grid-item>
            <n-grid-item :span="4" :s-span="24">
              <n-space>
                <n-button type="primary" @click="loadEpisodes">查询</n-button>
                <n-button secondary @click="resetFilters">重置</n-button>
              </n-space>
            </n-grid-item>
          </n-grid>
        </n-card>

        <n-data-table
          v-if="loading || episodes.length"
          :columns="columns"
          :data="episodes"
          :loading="loading"
          :row-key="rowKey"
          :pagination="{ pageSize: 8 }"
          :bordered="false"
        />
        <n-empty v-else description="暂无分集，请先在分集管理中创建或批量生成。" />
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { h, reactive, ref, watch } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NTag, useMessage } from 'naive-ui'
import { getProjectEpisodes } from '../api/episodes'
import type { ShortDramaEpisode, ShortDramaEpisodeStage, ShortDramaEpisodeStatus, ShortDramaEpisodeSubStatus } from '../types/episode'

const props = withDefaults(defineProps<{
  projectId: number | null
  modelValue: number | null
  episodeNo?: number | null
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
}>(), {
  episodeNo: null,
  placeholder: '请选择短剧分集',
  clearable: true,
  disabled: false,
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: number | null): void
  (event: 'change', value: ShortDramaEpisode | null): void
}>()

const message = useMessage()
const showModal = ref(false)
const loading = ref(false)
const episodes = ref<ShortDramaEpisode[]>([])
const selectedEpisode = ref<ShortDramaEpisode | null>(null)

const filters = reactive({
  keyword: '',
  stage: undefined as ShortDramaEpisodeStage | undefined,
  status: undefined as ShortDramaEpisodeStatus | undefined,
})

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

const stageOptions = Object.entries(stageMap).map(([value, label]) => ({ value, label }))
const statusOptions = Object.entries(statusMap).map(([value, label]) => ({ value, label }))

function stageTagType(stage: ShortDramaEpisodeStage) {
  if (stage === 'completed') return 'success'
  if (stage === 'media' || stage === 'localization') return 'warning'
  return 'info'
}

function subStatusLabel(status?: ShortDramaEpisodeSubStatus | null) {
  if (status === 'completed') return '已完成'
  if (status === 'processing') return '处理中'
  if (status === 'failed') return '失败'
  return '待处理'
}

function subStatusTagType(status?: ShortDramaEpisodeSubStatus | null) {
  if (status === 'completed') return 'success'
  if (status === 'processing') return 'info'
  if (status === 'failed') return 'error'
  return 'warning'
}

function rowKey(row: ShortDramaEpisode) {
  return row.id
}

function selectEpisode(row: ShortDramaEpisode) {
  selectedEpisode.value = row
  emit('update:modelValue', row.id)
  emit('change', row)
  showModal.value = false
}

function clearEpisode() {
  selectedEpisode.value = null
  emit('update:modelValue', null)
  emit('change', null)
}

async function loadEpisodes() {
  if (!props.projectId) return
  loading.value = true
  try {
    const response = await getProjectEpisodes(props.projectId, {
      keyword: filters.keyword || undefined,
      stage: filters.stage,
      status: filters.status,
      limit: 200,
    })
    if (response.code === 0) {
      episodes.value = response.data.items
      const current = episodes.value.find((item) => item.id === props.modelValue || item.episode_no === props.episodeNo)
      if (current) {
        selectedEpisode.value = current
        emit('change', current)
      } else if (props.modelValue) {
        selectedEpisode.value = null
        emit('change', null)
      }
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

function openModal() {
  if (props.disabled || !props.projectId) return
  showModal.value = true
  loadEpisodes()
}

const columns: DataTableColumns<ShortDramaEpisode> = [
  { title: '集数', key: 'episode_no', width: 90, render: (row) => `第 ${row.episode_no} 集` },
  { title: '分集标题', key: 'title', minWidth: 180 },
  {
    title: '当前阶段',
    key: 'stage',
    width: 120,
    render(row) {
      return h(NTag, { type: stageTagType(row.stage), bordered: false }, { default: () => stageMap[row.stage] })
    },
  },
  {
    title: '分镜状态',
    key: 'storyboard_status',
    width: 120,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.storyboard_status), bordered: false }, { default: () => subStatusLabel(row.storyboard_status) })
    },
  },
  {
    title: '本地化状态',
    key: 'localization_status',
    width: 130,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.localization_status), bordered: false }, { default: () => subStatusLabel(row.localization_status) })
    },
  },
  {
    title: '媒体状态',
    key: 'media_status',
    width: 120,
    render(row) {
      return h(NTag, { type: subStatusTagType(row.media_status), bordered: false }, { default: () => subStatusLabel(row.media_status) })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    fixed: 'right',
    render(row) {
      return h(NButton, { type: 'primary', size: 'small', onClick: () => selectEpisode(row) }, { default: () => '选择' })
    },
  },
]

watch(
  () => props.projectId,
  (value, oldValue) => {
    if (!value) {
      selectedEpisode.value = null
      episodes.value = []
      emit('update:modelValue', null)
      emit('change', null)
      return
    }
    if (oldValue && value !== oldValue) {
      selectedEpisode.value = null
      emit('update:modelValue', null)
      emit('change', null)
    }
    loadEpisodes()
  },
  { immediate: true },
)

watch(
  () => [props.modelValue, props.episodeNo] as const,
  () => {
    if (!props.modelValue && !props.episodeNo) {
      selectedEpisode.value = null
      return
    }
    if (props.projectId) loadEpisodes()
  },
)
</script>

<style scoped>
.episode-picker {
  width: 100%;
}

.picker-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}

.picker-card.disabled {
  opacity: 0.68;
}

.picker-main {
  min-width: 0;
}

.episode-title {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.episode-title.muted {
  color: #6b7280;
}

.episode-meta {
  margin-top: 5px;
  font-size: 12px;
  color: #64748b;
}

.episode-tags {
  margin-top: 8px;
}

.picker-actions {
  flex-shrink: 0;
}

.filter-card {
  background: #f8fafc;
}

:global(.episode-picker-modal .n-card__content) {
  padding-top: 10px;
}
</style>
