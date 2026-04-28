<template>
  <div class="project-picker">
    <div class="picker-card" :class="{ disabled }">
      <div class="picker-main">
        <template v-if="selectedProject">
          <div class="project-title">{{ selectedProject.name }}</div>
          <div class="project-meta">
            <span>{{ selectedProject.genre }}</span>
            <span>{{ selectedProject.target_market }}</span>
            <span>{{ getLabel('languages', selectedProject.language) }}</span>
            <span>{{ selectedProject.episode_count }} 集</span>
          </div>
          <n-space size="small" class="project-tags">
            <n-tag :type="stageTagType(selectedProject.stage)" size="small" :bordered="false">{{ getLabel('project_stages', selectedProject.stage) }}</n-tag>
            <n-tag :type="statusTagType(selectedProject.status)" size="small" :bordered="false">{{ getLabel('project_statuses', selectedProject.status) }}</n-tag>
          </n-space>
        </template>
        <template v-else>
          <div class="project-title muted">{{ placeholder }}</div>
          <div class="project-meta">选择短剧项目后，生成结果会通过 project_id 沉淀到对应项目。</div>
        </template>
      </div>
      <n-space class="picker-actions" size="small">
        <n-button size="small" secondary :disabled="disabled" @click="openModal">{{ selectedProject ? '重新选择' : '选择项目' }}</n-button>
        <n-button v-if="clearable && selectedProject" size="small" quaternary :disabled="disabled" @click="clearProject">清空</n-button>
      </n-space>
    </div>

    <n-modal v-model:show="showModal" preset="card" title="选择短剧项目" class="project-picker-modal" :style="{ width: '1800px' }">
      <!-- 真实业务里项目数量会增长，弹窗表格比下拉框更适合筛选、识别阶段和状态。 -->
      <n-space vertical size="medium">
        <n-card size="small" :bordered="false" class="filter-card">
          <n-grid :cols="24" :x-gap="12" :y-gap="12" responsive="screen">
            <n-grid-item :span="7" :s-span="24">
              <n-input v-model:value="filters.keyword" clearable placeholder="项目名称" @keyup.enter="loadProjects" />
            </n-grid-item>
            <n-grid-item :span="5" :s-span="12">
              <n-select v-model:value="filters.genre" clearable filterable placeholder="题材" :options="dictionaries.genres" />
            </n-grid-item>
            <n-grid-item :span="5" :s-span="12">
              <n-select v-model:value="filters.stage" clearable filterable placeholder="阶段" :options="dictionaries.project_stages" />
            </n-grid-item>
            <n-grid-item :span="5" :s-span="12">
              <n-select v-model:value="filters.status" clearable filterable placeholder="状态" :options="dictionaries.project_statuses" />
            </n-grid-item>
            <n-grid-item :span="2" :s-span="12">
              <n-space>
                <n-button type="primary" @click="loadProjects">查询</n-button>
                <n-button secondary @click="resetFilters">重置</n-button>
              </n-space>
            </n-grid-item>
          </n-grid>
        </n-card>

        <n-data-table
          v-if="loading || projects.length"
          :columns="columns"
          :data="projects"
          :loading="loading"
          :row-key="rowKey"
          :pagination="{ pageSize: 8 }"
          :bordered="false"
        />
        <n-empty v-else description="暂无短剧项目，请先在项目管理中创建。" />
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, reactive, ref, watch } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NTag, useMessage } from 'naive-ui'
import { getProjectDetail, getProjects } from '../api/projects'
import { useDictionaries } from '../composables/useDictionaries'
import type { ShortDramaProject, ShortDramaProjectStage, ShortDramaProjectStatus } from '../types/project'

const props = withDefaults(defineProps<{
  modelValue: number | null
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
}>(), {
  placeholder: '请选择短剧项目',
  clearable: true,
  disabled: false,
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: number | null): void
  (event: 'change', value: ShortDramaProject | null): void
}>()

const message = useMessage()
const { dictionaries, getLabel, loadDictionaries } = useDictionaries()
const showModal = ref(false)
const loading = ref(false)
const projects = ref<ShortDramaProject[]>([])
const selectedProject = ref<ShortDramaProject | null>(null)

const filters = reactive({
  keyword: '',
  genre: undefined,
  stage: undefined as ShortDramaProjectStage | undefined,
  status: undefined as ShortDramaProjectStatus | undefined,
})

function stageTagType(stage: ShortDramaProjectStage) {
  if (stage === 'completed') return 'success'
  if (stage === 'launch' || stage === 'material') return 'warning'
  return 'info'
}

function statusTagType(status: ShortDramaProjectStatus) {
  if (status === 'active') return 'success'
  if (status === 'archived') return 'default'
  if (status === 'paused') return 'warning'
  return 'info'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function selectProject(row: ShortDramaProject) {
  selectedProject.value = row
  emit('update:modelValue', row.id)
  emit('change', row)
  showModal.value = false
}

function clearProject() {
  selectedProject.value = null
  emit('update:modelValue', null)
  emit('change', null)
}

async function loadProjects() {
  loading.value = true
  try {
    const response = await getProjects({
      keyword: filters.keyword || undefined,
      genre: filters.genre || undefined,
      stage: filters.stage,
      status: filters.status,
      limit: 100,
    })
    if (response.code === 0) {
      projects.value = response.data.items
      const current = projects.value.find((item) => item.id === props.modelValue)
      if (current) selectedProject.value = current
    }
  } catch {
    message.error('短剧项目列表加载失败')
  } finally {
    loading.value = false
  }
}

async function loadSelectedProject(id: number) {
  try {
    const response = await getProjectDetail(id)
    if (response.code === 0) {
      selectedProject.value = response.data
      emit('change', response.data)
    }
  } catch {
    selectedProject.value = null
    emit('change', null)
    message.warning('未找到对应短剧项目，可手动选择。')
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.genre = undefined
  filters.stage = undefined
  filters.status = undefined
  loadProjects()
}

function openModal() {
  if (props.disabled) return
  showModal.value = true
  loadProjects()
}

const columns: DataTableColumns<ShortDramaProject> = [
  { title: '项目名称', key: 'name', minWidth: 200 },
  { title: '题材类型', key: 'genre', width: 110 },
  { title: '目标市场', key: 'target_market', width: 110 },
  { title: '主语言', key: 'language', width: 130, render: (row) => getLabel('languages', row.language) },
  { title: '集数', key: 'episode_count', width: 80 },
  {
    title: '当前阶段',
    key: 'stage',
    width: 120,
    render(row) {
      return h(NTag, { type: stageTagType(row.stage), bordered: false }, { default: () => getLabel('project_stages', row.stage) })
    },
  },
  {
    title: '项目状态',
    key: 'status',
    width: 110,
    render(row) {
      return h(NTag, { type: statusTagType(row.status), bordered: false }, { default: () => getLabel('project_statuses', row.status) })
    },
  },
  { title: '更新时间', key: 'updated_at', width: 170, render: (row) => formatTime(row.updated_at) },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    fixed: 'right',
    render(row) {
      return h(NButton, { type: 'primary', size: 'small', onClick: () => selectProject(row) }, { default: () => '选择' })
    },
  },
]

function rowKey(row: ShortDramaProject) {
  return row.id
}

watch(
  () => props.modelValue,
  (value) => {
    if (!value) {
      selectedProject.value = null
      emit('change', null)
      return
    }
    if (selectedProject.value?.id !== value) loadSelectedProject(value)
  },
  { immediate: true },
)

onMounted(async () => {
  await loadDictionaries()
  await loadProjects()
})
</script>

<style scoped>
.project-picker {
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
  opacity: 0.6;
  cursor: not-allowed;
}

.picker-main {
  min-width: 0;
}

.project-title {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.project-title.muted {
  color: #6b7280;
}

.project-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 5px;
  font-size: 12px;
  color: #64748b;
}

.project-tags {
  margin-top: 8px;
}

.picker-actions {
  flex-shrink: 0;
}

.filter-card {
  background: #f8fafc;
}

:global(.project-picker-modal .n-card__content) {
  padding-top: 10px;
}

:global(.n-data-table) {
  min-height: 360px;
}

:global(.n-empty) {
  padding: 64px 0;
}
</style>
