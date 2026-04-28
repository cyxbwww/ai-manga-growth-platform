<template>
  <div class="module-page content-planning-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="策划输入" :bordered="false">
            <n-form :model="form" label-placement="top">
              <n-form-item label="所属短剧项目">
                <ProjectPicker
                  v-model="selectedProjectId"
                  placeholder="建议选择短剧项目，方便沉淀到完整生产链路"
                  @change="handleProjectChange"
                />
              </n-form-item>
              <n-button v-if="selectedProjectId" tertiary size="small" class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}`)">
                返回项目详情
              </n-button>
              <n-form-item label="项目名称">
                <n-input
                  v-model:value="form.projectName"
                  placeholder="例如：逆袭千金的北美爆款短剧"
                  @update:value="markFieldTouched('projectName')"
                />
              </n-form-item>
              <n-form-item label="短剧题材">
                <n-select
                  v-model:value="form.genre"
                  filterable
                  label-field="label"
                  value-field="value"
                  placeholder="请选择短剧题材"
                  :options="dictionaries.genres"
                  @update:value="markFieldTouched('genre')"
                />
              </n-form-item>
              <n-form-item label="目标市场">
                <n-select
                  v-model:value="form.market"
                  filterable
                  label-field="label"
                  value-field="value"
                  placeholder="请选择目标市场"
                  :options="dictionaries.markets"
                  @update:value="markFieldTouched('market')"
                />
              </n-form-item>
              <n-form-item label="目标语言">
                <n-select
                  v-model:value="form.language"
                  filterable
                  label-field="label"
                  value-field="value"
                  placeholder="请选择目标语言"
                  :options="dictionaries.languages"
                  @update:value="markFieldTouched('language')"
                />
              </n-form-item>
              <n-form-item label="单集目标时长">
                <n-radio-group v-model:value="form.duration">
                  <n-space>
                    <n-radio-button value="30秒">30秒</n-radio-button>
                    <n-radio-button value="60秒">60秒</n-radio-button>
                    <n-radio-button value="90秒">90秒</n-radio-button>
                  </n-space>
                </n-radio-group>
              </n-form-item>
              <n-form-item label="核心卖点">
                <n-input
                  v-model:value="form.sellingPoint"
                  type="textarea"
                  :autosize="{ minRows: 5, maxRows: 8 }"
                  placeholder="输入主角设定、反转点、情绪卖点或目标受众痛点"
                  @update:value="markFieldTouched('sellingPoint')"
                />
              </n-form-item>
              <n-button type="primary" block size="large" :loading="loading" @click="handleGenerate">
                生成策划方案
              </n-button>
            </n-form>
          </n-card>

          <n-card title="历史记录" :bordered="false">
            <n-list v-if="history.length" hoverable clickable>
              <n-list-item v-for="item in history" :key="item.id" @click="selectHistory(item)">
                <n-thing :title="item.projectName" :description="formatTime(item.createdAt)">
                  <template #header-extra>
                    <n-space size="small">
                      <n-tag type="info" bordered>{{ item.market }}</n-tag>
                      <n-tag type="success" bordered>{{ getLabel('languages', item.language) }}</n-tag>
                    </n-space>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
            <n-empty v-else description="暂无历史记录，生成后会自动保存。" />
          </n-card>
        </n-space>
      </n-grid-item>

      <n-grid-item :span="16" :s-span="24">
        <n-spin :show="loading">
          <n-card title="AI策划结果" :bordered="false" class="result-card">
            <template #header-extra>
              <n-radio-group v-if="result?.bilingual" v-model:value="displayLanguage" size="small">
                <n-radio-button value="zh">中文</n-radio-button>
                <n-radio-button value="target">{{ getLabel('languages', result.bilingual.target.language) || '目标语言' }}</n-radio-button>
              </n-radio-group>
            </template>

            <template v-if="result">
              <div class="result-title">{{ contentView.title }}</div>
              <n-grid :cols="2" :x-gap="14" :y-gap="14" responsive="screen">
                <n-grid-item>
                  <InfoBlock title="故事定位" :content="contentView.positioning" />
                </n-grid-item>
                <n-grid-item>
                  <InfoBlock title="目标用户" :content="contentView.targetAudience" />
                </n-grid-item>
                <n-grid-item>
                  <InfoBlock title="核心冲突" :content="contentView.coreConflict" />
                </n-grid-item>
                <n-grid-item>
                  <InfoBlock title="情绪钩子" :content="contentView.emotionHook" />
                </n-grid-item>
              </n-grid>
              <n-card size="small" class="inner-card" title="3秒开头建议">
                <p>{{ contentView.openingHook }}</p>
              </n-card>
              <n-grid :cols="3" :x-gap="14" :y-gap="14" responsive="screen">
                <n-grid-item>
                  <ListBlock title="爽点/泪点/反转点" :items="contentView.highlights" />
                </n-grid-item>
                <n-grid-item>
                  <ListBlock title="适合投放平台" :items="contentView.platforms" tag-type="success" />
                </n-grid-item>
                <n-grid-item>
                  <ListBlock title="AI策划建议" :items="contentView.suggestions" tag-type="info" />
                </n-grid-item>
              </n-grid>
              <div class="next-step-row">
                <n-button type="primary" :disabled="Boolean(outlineDisabledReason)" :loading="outlineLoading" @click="openOutlineModal">生成分集大纲</n-button>
                <n-button type="primary" secondary @click="router.push('/script-polish')">进入剧本打磨</n-button>
              </div>
              <div v-if="outlineDisabledReason" class="outline-disabled-tip">{{ outlineDisabledReason }}</div>
              <n-alert v-if="outlineResult" type="success" :bordered="false" class="outline-result">
                {{ outlineSuccessText }}
                <template #action>
                  <n-button size="small" type="primary" secondary @click="goEpisodeManagement">查看分集管理</n-button>
                </template>
              </n-alert>
            </template>
            <n-empty v-else description="填写左侧信息后生成策划方案，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>
    </n-grid>

    <n-modal v-model:show="showOutlineModal" preset="card" title="生成分集大纲" class="outline-modal">
      <p class="outline-desc">系统会基于当前内容策划结果生成分集大纲初稿，优先使用 DeepSeek 生成，失败时自动使用规则兜底，保证流程可用。生成后可在分集管理中逐集调整。</p>
      <n-form :model="outlineForm" label-placement="top">
        <n-form-item label="生成集数">
          <n-input-number v-model:value="outlineForm.episode_count" :min="1" :max="30" class="full-width" />
        </n-form-item>
        <n-form-item label="起始集数">
          <n-input-number v-model:value="outlineForm.start_episode_no" :min="1" :max="500" class="full-width" />
        </n-form-item>
        <n-form-item label="是否覆盖已有分集">
          <n-space vertical size="small">
            <n-switch v-model:value="outlineForm.overwrite" />
            <n-text depth="3">关闭时，已存在的同集数会跳过；开启时，会覆盖同集数标题和摘要。</n-text>
          </n-space>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button secondary @click="showOutlineModal = false">取消</n-button>
          <n-button type="primary" :loading="outlineLoading" @click="submitOutline">开始生成</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NTag, useMessage } from 'naive-ui'
import { createContentPlan, getContentPlanHistory } from '../api/content'
import { generateEpisodeOutline } from '../api/episodes'
import ProjectPicker from '../components/ProjectPicker.vue'
import { useDictionaries } from '../composables/useDictionaries'
import { usePipelineStore } from '../stores/pipeline'
import type { ContentPlanBilingualFields, ContentPlanHistoryItem, ContentPlanRequest, ContentPlanResult } from '../types/content'
import type { EpisodeOutlineGenerateResponse } from '../types/episode'
import type { ShortDramaProject } from '../types/project'

type ProjectChangePayload = ShortDramaProject & {
  primary_language?: string
}

type LegacyContentPlanHistoryItem = ContentPlanHistoryItem & {
  project_name?: string
  title?: string
  selling_point?: string
}

const form = reactive<ContentPlanRequest>({
  projectName: '逆袭千金的北美爆款短剧',
  genre: '都市逆袭',
  market: '北美',
  language: 'en-US',
  duration: '60秒',
  sellingPoint: '女主被家族抛弃后用商业能力反击，前3秒需要强冲突，结尾留下复仇反转。',
})

const loading = ref(false)
const result = ref<ContentPlanResult | null>(null)
const history = ref<ContentPlanHistoryItem[]>([])
const displayLanguage = ref<'zh' | 'target'>('zh')
const message = useMessage()
const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const { dictionaries, loadDictionaries, getLabel } = useDictionaries()
const selectedProjectId = ref<number | null>(null)
const showOutlineModal = ref(false)
const outlineLoading = ref(false)
const outlineResult = ref<EpisodeOutlineGenerateResponse | null>(null)
const outlineForm = reactive({
  episode_count: 10,
  start_episode_no: 1,
  overwrite: false,
})
const touchedFields = reactive<Record<'projectName' | 'genre' | 'market' | 'language' | 'sellingPoint', boolean>>({
  projectName: false,
  genre: false,
  market: false,
  language: false,
  sellingPoint: false,
})

const contentView = computed<ContentPlanBilingualFields>(() => {
  // 旧历史数据没有 bilingual 时直接使用顶层字段，确保向后兼容。
  if (!result.value?.bilingual) return result.value as ContentPlanResult
  return displayLanguage.value === 'target' ? result.value.bilingual.target : result.value.bilingual.zh
})

const currentContentPlanId = computed(() => result.value?.recordId || pipeline.contentPlanId || null)

const outlineDisabledReason = computed(() => {
  if (!selectedProjectId.value) return '请先选择短剧项目。'
  if (!result.value || !currentContentPlanId.value) return '请先生成或选择一条内容策划结果。'
  return ''
})

const outlineSuccessText = computed(() => {
  if (!outlineResult.value) return ''
  return formatOutlineSuccess(outlineResult.value)
})

const InfoBlock = defineComponent({
  props: { title: { type: String, required: true }, content: { type: String, required: true } },
  setup(props) {
    return () => h(NCard, { size: 'small', class: 'inner-card card', title: props.title }, { default: () => h('p', { class: 'card-content' }, props.content) })
  },
})

const ListBlock = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array<string>, required: true },
    tagType: { type: String, default: 'warning' },
  },
  setup(props) {
    return () =>
      h(NCard, { size: 'small', class: 'inner-card card', title: props.title }, {
        default: () =>
          h(
            'div',
            { class: 'tag-container card-content' },
            props.items.map((item) =>
              h('div', { class: 'tag-row', style: { marginBottom: '10px' } }, [
                h(
                  NTag,
                  {
                    class: 'content-tag',
                    type: props.tagType as 'default',
                    bordered: false,
                    style: {
                      display: 'flex',
                      width: '100%',
                      maxWidth: '100%',
                      height: 'auto',
                      paddingTop: '5px',
                      paddingBottom: '5px',
                      marginBottom: '0',
                      whiteSpace: 'normal',
                    },
                  },
                  { default: () => h('span', { class: 'tag-text', style: { display: 'block', width: '100%', lineHeight: '1.7' } }, item) },
                ),
              ]),
            ),
          ),
      })
  },
})

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function markFieldTouched(field: keyof typeof touchedFields) {
  touchedFields[field] = true
}

function shouldHydrateField(field: keyof typeof touchedFields, currentValue?: string | null) {
  return !touchedFields[field] || !String(currentValue || '').trim()
}

function hydrateField(field: keyof ContentPlanRequest, value?: string | null) {
  if (!value) return
  if (field === 'projectName' && shouldHydrateField('projectName', form.projectName)) form.projectName = value
  if (field === 'genre' && shouldHydrateField('genre', form.genre)) form.genre = value
  if (field === 'market' && shouldHydrateField('market', form.market)) form.market = value
  if (field === 'language' && shouldHydrateField('language', form.language)) form.language = value
  if (field === 'sellingPoint' && shouldHydrateField('sellingPoint', form.sellingPoint)) form.sellingPoint = value
}

function handleProjectChange(project: ProjectChangePayload | null) {
  if (!project) return
  // 选择项目后只同步未手动编辑过的字段，避免覆盖用户在页面内补充的策划输入。
  hydrateField('projectName', project.name)
  hydrateField('genre', project.genre)
  hydrateField('market', project.target_market)
  hydrateField('language', project.primary_language || project.language)
  hydrateField('sellingPoint', project.description)
  message.success('已同步短剧项目基础信息。')
}

function restoreHistoryField(field: keyof typeof touchedFields, value?: string | null) {
  const nextValue = value || ''
  if (field === 'projectName') form.projectName = nextValue
  if (field === 'genre') form.genre = nextValue
  if (field === 'market') form.market = nextValue
  if (field === 'language') form.language = nextValue
  if (field === 'sellingPoint') form.sellingPoint = nextValue
  // 历史记录自身字段优先级高于项目回填；空字段仍允许 ProjectPicker 后续补齐。
  touchedFields[field] = true
}

function restoreHistoryForm(item: ContentPlanHistoryItem) {
  const legacyItem = item as LegacyContentPlanHistoryItem
  restoreHistoryField('projectName', item.projectName || legacyItem.project_name || legacyItem.title || item.result?.title)
  restoreHistoryField('genre', item.genre)
  restoreHistoryField('market', item.market)
  restoreHistoryField('language', item.language)
  form.duration = item.duration || ''
  restoreHistoryField('sellingPoint', item.sellingPoint || legacyItem.selling_point)
}

async function restoreHistoryProject(projectId?: number | null) {
  const nextProjectId = projectId || null
  if (nextProjectId && selectedProjectId.value === nextProjectId) {
    selectedProjectId.value = null
    await nextTick()
  }
  selectedProjectId.value = nextProjectId
}

async function selectHistory(item: ContentPlanHistoryItem) {
  result.value = item.result
  restoreHistoryForm(item)
  await restoreHistoryProject(item.project_id)
  pipeline.setContentPlanId(item.recordId || item.id)
  outlineResult.value = null
  displayLanguage.value = 'zh'
  message.success('已加载历史策划结果')
}

async function loadHistory() {
  const response = await getContentPlanHistory()
  if (response.code === 0) {
    history.value = response.data
  }
}

async function handleGenerate() {
  if (!form.projectName.trim() || !form.sellingPoint.trim()) {
    message.warning('请填写项目名称和核心卖点')
    return
  }
  if (!selectedProjectId.value) {
    message.warning('建议选择短剧项目，方便沉淀到完整生产链路。')
  }

  loading.value = true
  try {
    const response = await createContentPlan({ ...form, project_id: selectedProjectId.value })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setContentPlanId(response.data.recordId)
      outlineResult.value = null
      displayLanguage.value = 'zh'
      await loadHistory()
      message.success(selectedProjectId.value ? '已生成并归属到当前短剧项目。' : '策划方案已生成并保存')
    }
  } catch {
    message.error('策划方案生成失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

function openOutlineModal() {
  if (outlineDisabledReason.value) {
    message.warning(outlineDisabledReason.value)
    return
  }
  outlineResult.value = null
  showOutlineModal.value = true
}

function formatOutlineSuccess(data: EpisodeOutlineGenerateResponse) {
  const countText = `${data.created_count} 条分集大纲，更新 ${data.updated_count} 条，跳过 ${data.skipped_count} 条。`
  if (data.generation_source === 'deepseek') return `已使用 DeepSeek 生成 ${countText}`
  if (data.generation_source === 'rule_fallback') return `DeepSeek 不可用或返回异常，已使用规则兜底生成 ${countText}`
  return `已生成 ${countText}`
}

async function submitOutline() {
  if (outlineDisabledReason.value || !selectedProjectId.value || !currentContentPlanId.value) {
    message.warning(outlineDisabledReason.value || '请先生成或选择一条内容策划结果。')
    return
  }
  outlineLoading.value = true
  try {
    const response = await generateEpisodeOutline(selectedProjectId.value, {
      content_plan_id: currentContentPlanId.value,
      episode_count: outlineForm.episode_count,
      start_episode_no: outlineForm.start_episode_no,
      overwrite: outlineForm.overwrite,
    })
    if (response.code === 0) {
      outlineResult.value = response.data
      showOutlineModal.value = false
      message.success(formatOutlineSuccess(response.data))
    }
  } catch {
    message.error('分集大纲生成失败，请确认后端服务已启动。')
  } finally {
    outlineLoading.value = false
  }
}

function goEpisodeManagement() {
  if (!selectedProjectId.value) return
  router.push(`/projects/${selectedProjectId.value}/episodes`)
}

onMounted(async () => {
  await loadDictionaries()
  // 从项目详情页进入时，先写入 projectId，ProjectPicker 会负责加载并回显项目信息。
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) selectedProjectId.value = queryProjectId
  await loadHistory()
})
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.result-card {
  min-height: 620px;
}

.project-back-btn {
  margin: -6px 0 14px;
}

.result-card :deep(.n-grid-item) {
  min-width: 0;
}

.result-title {
  margin-bottom: 16px;
  color: #111827;
  font-size: 24px;
  font-weight: 800;
}

.inner-card {
  min-width: 0;
  margin-bottom: 14px;
  background: #fbfcff;
}

.card {
  min-width: 0;
}

.inner-card :deep(.n-card__content) {
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
}

.card-content {
  max-width: 100%;
  max-height: 140px;
  overflow-x: hidden;
  overflow-y: auto;
  white-space: normal !important;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.tag-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
}

.tag-row {
  display: flex;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  margin-bottom: 10px !important;
}

.tag-row:last-child {
  margin-bottom: 0 !important;
}

.tag-container :deep(.n-tag) {
  display: inline-flex;
  flex: 1 1 100%;
  align-items: flex-start;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  height: auto;
  min-height: 28px;
  padding-top: 4px;
  padding-bottom: 4px;
  white-space: normal !important;
  overflow: hidden !important;
}

.tag-container :deep(.n-tag__content) {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow: hidden !important;
  text-overflow: clip !important;
  white-space: normal !important;
  word-break: break-word;
  overflow-wrap: anywhere;
  line-height: 1.5;
}

.tag-text {
  display: block;
  width: 100%;
  max-width: 100%;
  white-space: normal !important;
  word-break: break-word;
  overflow-wrap: anywhere;
  line-height: 1.6;
}

:global(.content-planning-page .tag-container .n-tag) {
  display: flex !important;
  width: 100% !important;
  max-width: 100% !important;
  height: auto !important;
  min-height: 28px;
  margin-bottom: 0 !important;
  padding-top: 4px !important;
  padding-bottom: 4px !important;
  box-sizing: border-box;
  overflow: hidden !important;
  white-space: normal !important;
}

:global(.content-planning-page .tag-container .n-tag__content) {
  display: block !important;
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  overflow: hidden !important;
  text-overflow: clip !important;
  white-space: normal !important;
  word-break: break-word !important;
  overflow-wrap: anywhere !important;
  line-height: 1.6 !important;
}

:global(.content-planning-page .tag-container .tag-text) {
  display: block;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  white-space: normal !important;
  word-break: break-word !important;
  overflow-wrap: anywhere !important;
  line-height: 1.6;
}

.inner-card p {
  margin: 0;
  color: #374151;
  line-height: 1.7;
}

.next-step-row {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

.outline-disabled-tip {
  margin-top: 8px;
  color: #6b7280;
  font-size: 13px;
  text-align: right;
}

.outline-result {
  margin-top: 14px;
}

.outline-modal {
  width: min(520px, calc(100vw - 32px));
}

.outline-desc {
  margin: 0 0 16px;
  color: #4b5563;
  line-height: 1.7;
}

.full-width {
  width: 100%;
}
</style>
