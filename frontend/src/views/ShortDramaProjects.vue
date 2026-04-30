<template>
  <div class="projects-page">
    <n-card bordered class="intro-card">
      <div class="intro-header">
        <div>
          <h2>短剧项目管理</h2>
          <p>以短剧项目为主线，串联内容策划、剧本打磨、AI分镜、本地化、广告素材、媒体资源和投放分析。</p>
        </div>
        <n-button type="primary" size="large" @click="openCreateModal">新建项目</n-button>
      </div>
    </n-card>

    <n-card title="项目列表" bordered class="table-card">
      <template #header-extra>
        <n-button size="small" secondary @click="loadProjects">刷新</n-button>
      </template>

      <div class="filter-bar">
        <n-input v-model:value="filters.keyword" clearable placeholder="搜索项目名称或简介" />
        <n-select
          v-model:value="filters.genre"
          clearable
          filterable
          label-field="label"
          value-field="value"
          placeholder="请选择题材类型"
          :options="dictionaries.genres"
        />
        <n-select
          v-model:value="filters.stage"
          clearable
          filterable
          label-field="label"
          value-field="value"
          placeholder="请选择当前阶段"
          :options="dictionaries.project_stages"
        />
        <n-select
          v-model:value="filters.status"
          clearable
          filterable
          label-field="label"
          value-field="value"
          placeholder="请选择项目状态"
          :options="dictionaries.project_statuses"
        />
        <n-button type="primary" @click="loadProjects">查询</n-button>
        <n-button secondary @click="resetFilters">重置</n-button>
      </div>

      <n-data-table
        :columns="columns"
        :data="projects"
        :loading="loading"
        :bordered="false"
        :single-line="false"
        :pagination="false"
        class="project-table"
      >
        <template #empty>
          <n-empty description="暂无短剧项目，点击右上角新建项目。" />
        </template>
      </n-data-table>

      <div class="table-footer">
        <span>共 {{ total }} 个项目</span>
      </div>
    </n-card>

    <n-modal
      v-model:show="showModal"
      preset="card"
      :title="editingId ? '编辑短剧项目' : '新建短剧项目'"
      class="project-modal"
      :style="{ width: '70%' }"
    >
      <n-form :model="form" label-placement="top">
        <n-grid :cols="2" :x-gap="16">
          <n-form-item-gi label="项目名称">
            <n-input v-model:value="form.name" placeholder="请输入项目名称" />
          </n-form-item-gi>
          <n-form-item-gi label="题材类型">
            <n-select
              v-model:value="form.genre"
              filterable
              label-field="label"
              value-field="value"
              :options="dictionaries.genres"
              placeholder="请选择题材类型"
            />
          </n-form-item-gi>
          <n-form-item-gi label="目标市场">
            <n-select
              v-model:value="form.target_market"
              filterable
              label-field="label"
              value-field="value"
              :options="dictionaries.markets"
              placeholder="请选择目标市场"
            />
          </n-form-item-gi>
          <n-form-item-gi label="主语言">
            <n-select
              v-model:value="form.language"
              filterable
              label-field="label"
              value-field="value"
              :options="dictionaries.languages"
              placeholder="请选择主语言"
            />
          </n-form-item-gi>
          <n-form-item-gi label="计划集数">
            <n-input-number v-model:value="form.episode_count" :min="1" :max="500" class="full-width" />
          </n-form-item-gi>
          <n-form-item-gi label="当前阶段">
            <n-select
              v-model:value="form.stage"
              filterable
              label-field="label"
              value-field="value"
              :options="dictionaries.project_stages"
              placeholder="请选择当前阶段"
            />
          </n-form-item-gi>
          <n-form-item-gi label="负责人">
            <n-input v-model:value="form.owner" placeholder="请输入负责人" />
          </n-form-item-gi>
          <n-form-item-gi label="优先级">
            <n-select
              v-model:value="form.priority"
              filterable
              label-field="label"
              value-field="value"
              :options="dictionaries.priorities"
              placeholder="请选择优先级"
            />
          </n-form-item-gi>
          <n-form-item-gi label="项目状态">
            <n-select
              v-model:value="form.status"
              filterable
              label-field="label"
              value-field="value"
              :options="dictionaries.project_statuses"
              placeholder="请选择项目状态"
            />
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="项目简介">
          <n-input v-model:value="form.description" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" placeholder="请输入项目简介" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button secondary @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitProject">{{ editingId ? '保存修改' : '创建项目' }}</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NPopconfirm, NSpace, NTag, NTooltip, useMessage } from 'naive-ui'
import { archiveProject, createProject, getProjects, updateProject } from '../api/projects'
import { useDictionaries } from '../composables/useDictionaries'
import type {
  ShortDramaProject,
  ShortDramaProjectCreate,
  ShortDramaProjectPriority,
  ShortDramaProjectStage,
  ShortDramaProjectStatus,
} from '../types/project'

const message = useMessage()
const router = useRouter()
const { dictionaries, getLabel, loadDictionaries } = useDictionaries()
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const editingId = ref<number | null>(null)
const projects = ref<ShortDramaProject[]>([])
const total = ref(0)

// 筛选条件独立维护，避免影响新建/编辑表单。
const filters = reactive({
  keyword: '',
  genre: undefined,
  stage: undefined as ShortDramaProjectStage | undefined,
  status: undefined as ShortDramaProjectStatus | undefined,
})

const defaultForm: ShortDramaProjectCreate = {
  name: '',
  genre: undefined,
  target_market: undefined,
  language: 'zh-CN',
  episode_count: 60,
  stage: 'planning',
  description: '',
  owner: '',
  priority: 'medium',
  status: 'active',
}

const form = reactive<ShortDramaProjectCreate>({ ...defaultForm })

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

function priorityTagType(priority: ShortDramaProjectPriority) {
  if (priority === 'high') return 'error'
  if (priority === 'low') return 'default'
  return 'warning'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

const columns: DataTableColumns<ShortDramaProject> = [
  {
    title: '项目名称',
    key: 'name',
    minWidth: 220,
    render(row) {
      return h('div', { class: 'project-name-cell' }, [
        h(NTooltip,  { trigger: 'hover', placement: 'top-start', style: 'width: 600px' }, {
          trigger: () =>
            h(
              'div',
              { class: 'project-name' },
              row.name
            ),
          default: () => row.description || '暂无项目简介'
        }),
      ])
    },
  },
  { title: '题材类型', key: 'genre', width: 120 },
  { title: '目标市场', key: 'target_market', width: 110 },
  { title: '主语言', key: 'language', width: 140, render: (row) => getLabel('languages', row.language) },
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
  {
    title: '优先级',
    key: 'priority',
    width: 90,
    render(row) {
      return h(NTag, { type: priorityTagType(row.priority), bordered: false }, { default: () => getLabel('priorities', row.priority) })
    },
  },
  { title: '负责人', key: 'owner', width: 110, render: (row) => row.owner || '-' },
  { title: '更新时间', key: 'updated_at', width: 170, render: (row) => formatTime(row.updated_at) },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    fixed: 'right',
    render(row) {
      return h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', secondary: true, onClick: () => router.push(`/projects/${row.id}`) }, { default: () => '查看详情' }),
          h(NButton, { size: 'small', secondary: true, onClick: () => openEditModal(row) }, { default: () => '编辑' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => archive(row.id) },
            {
              trigger: () => h(NButton, { size: 'small', tertiary: true, disabled: row.status === 'archived' }, { default: () => '归档' }),
              default: () => '确认归档该项目？',
            },
          ),
        ],
      })
    },
  },
]

async function loadProjects() {
  loading.value = true
  try {
    const res = await getProjects({
      keyword: filters.keyword || undefined,
      genre: filters.genre || undefined,
      stage: filters.stage || undefined,
      status: filters.status || undefined,
      skip: 0,
      limit: 50,
    })
    if (res.code === 0) {
      projects.value = res.data.items
      total.value = res.data.total
    }
  } catch {
    message.error('项目列表加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.genre = undefined
  filters.stage = undefined
  filters.status = undefined
  loadProjects()
}

function resetForm() {
  Object.assign(form, defaultForm)
}

function openCreateModal() {
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEditModal(row: ShortDramaProject) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    genre: row.genre,
    target_market: row.target_market,
    language: row.language,
    episode_count: row.episode_count,
    stage: row.stage,
    description: row.description || '',
    owner: row.owner || '',
    priority: row.priority,
    status: row.status,
  })
  showModal.value = true
}

async function submitProject() {
  if (!form.name.trim() || !form.genre?.trim() || !form.target_market?.trim() || !form.language.trim()) {
    message.warning('请填写项目名称、题材类型、目标市场和主语言')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateProject(editingId.value, { ...form })
      message.success('项目已更新')
    } else {
      await createProject({ ...form })
      message.success('项目已创建')
    }
    showModal.value = false
    await loadProjects()
  } catch {
    message.error('项目保存失败，请检查后端接口')
  } finally {
    saving.value = false
  }
}

async function archive(id: number) {
  try {
    await archiveProject(id)
    message.success('项目已归档')
    await loadProjects()
  } catch {
    message.error('项目归档失败')
  }
}

onMounted(async () => {
  await loadDictionaries()
  await loadProjects()
})
</script>

<style scoped>
.projects-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.intro-card {
  background: linear-gradient(135deg, #f8fafc, #eef6ff);
}

.intro-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.intro-header h2 {
  margin: 0;
  color: #111827;
  font-size: 22px;
}

.intro-header p {
  margin: 8px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.table-card {
  min-width: 0;
}

.filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) repeat(3, minmax(140px, 1fr)) auto auto;
  gap: 12px;
  margin-bottom: 16px;
}

.project-table {
  min-height: 360px;
}

.project-name-cell {
  min-width: 0;
}

.project-name {
  color: #111827;
  font-weight: 700;
}

.project-desc {
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  color: #6b7280;
  font-size: 13px;
}

.project-modal {
  width: min(760px, 92vw);
}

.full-width {
  width: 100%;
}

@media (max-width: 1100px) {
  .filter-bar {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .intro-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
