<template>
  <div class="module-page">
    <n-card title="本地化配置" :bordered="false" class="config-card">
      <div class="config-card-content">
        <div v-if="selectedProjectId">
          <n-button secondary @click="router.push(`/projects/${selectedProjectId}`)">返回项目详情</n-button>
          <n-button secondary class="episode-back-btn" @click="router.push(`/projects/${selectedProjectId}/episodes`)">
            返回分集列表
          </n-button>
        </div>
        <div class="project-bind-row">
          <n-form-item label="所属短剧项目" class="project-select">
            <ProjectPicker
              v-model="selectedProjectId"
              placeholder="建议选择短剧项目，方便沉淀到完整生产链路"
              @change="handleProjectChange"
            />
          </n-form-item>
          <n-form-item label="所属分集" class="project-select">
            <EpisodePicker
              v-model="episodeId"
              :project-id="selectedProjectId"
              :episode-no="episodeNo"
              placeholder="请选择要本地化的具体分集"
              @change="handleEpisodeChange"
            />
          </n-form-item>
        </div>
      </div>
      <n-grid :cols="24" :x-gap="14" :y-gap="14" responsive="screen">
        <n-grid-item :span="5" :s-span="24">
          <n-form-item label="目标市场">
            <n-select
              v-model:value="form.market"
              filterable
              label-field="label"
              value-field="value"
              placeholder="请选择目标市场"
              :options="dictionaries.markets"
              @update:value="targetMarketTouched = true"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item :span="5" :s-span="24">
          <n-form-item label="目标语言">
            <n-select
              v-model:value="form.language"
              filterable
              label-field="label"
              value-field="value"
              placeholder="请选择目标语言"
              :options="dictionaries.languages"
              @update:value="targetLanguageTouched = true"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item :span="7" :s-span="24">
          <n-form-item label="本地化策略"><n-select v-model:value="form.strategy" :options="strategyOptions" /></n-form-item>
        </n-grid-item>
        <n-grid-item :span="4" :s-span="24">
          <n-form-item label="操作">
            <n-button type="primary" block :loading="loading" @click="handleProcess">开始本地化</n-button>
          </n-form-item>
        </n-grid-item>
      </n-grid>
      <n-form-item label="本地化输入内容" class="source-input-item">
        <n-input
          v-model:value="form.source_text"
          type="textarea"
          :autosize="{ minRows: 5, maxRows: 10 }"
          placeholder="选择项目和分集后会自动引用分集级剧本打磨结果；也可以手动填写中文剧本或分集大纲。"
          @update:value="handleSourceTextUpdate"
        />
      </n-form-item>
      <n-alert :type="sourceNoticeType" :bordered="false" class="source-notice">
        {{ sourceNotice }}
      </n-alert>
    </n-card>

    <n-alert type="info" :bordered="false">
      中文用于内部审核，目标语言用于海外投放。当前页面可独立使用，也可从上一环节进入以自动绑定剧本或分镜来源。
    </n-alert>

    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="17" :s-span="24">
        <n-spin :show="loading">
          <n-card title="字幕本地化结果" :bordered="false" class="result-card">
            <template v-if="result">
              <div class="localization-summary">
                <div>
                  <div class="result-title">{{ result.market }} / {{ result.language }} / {{ result.strategy }}</div>
                  <div class="result-copy">本地化不是逐字翻译，而是围绕情绪、文化语境和转化目标重写表达。</div>
                </div>
                <n-tag type="success" bordered>已保存</n-tag>
              </div>

              <n-data-table :columns="columns" :data="result.subtitles" :bordered="false" :single-line="false" />

              <n-card size="small" title="本地化改写对比" class="compare-card">
                <n-grid :cols="3" :x-gap="14" :y-gap="14" responsive="screen">
                  <n-grid-item>
                    <div class="compare-label">中文原文</div>
                    <div class="compare-text">你怎么能这样对我？</div>
                  </n-grid-item>
                  <n-grid-item>
                    <div class="compare-label">直译</div>
                    <div class="compare-text">How could you do this to me?</div>
                  </n-grid-item>
                  <n-grid-item>
                    <div class="compare-label">本地化改写</div>
                    <div class="compare-text strong">After everything I gave up for you, this is how you repay me?</div>
                  </n-grid-item>
                </n-grid>
              </n-card>

              <div class="next-step-row">
                <n-button type="primary" secondary @click="goWithContext('/ad-materials')">进入海外投放素材</n-button>
              </div>
            </template>
            <n-empty v-else description="选择配置后开始本地化，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>

      <n-grid-item :span="7" :s-span="24">
        <n-space vertical size="large">
          <n-card title="海外版本生产流程" :bordered="false" class="workflow-card">
            <n-timeline v-if="result">
              <n-timeline-item
                v-for="item in result.workflow"
                :key="item.step"
                :type="workflowType(item.status)"
                :title="item.step"
                :content="`${item.status} - ${item.description}`"
              />
            </n-timeline>
            <n-empty v-else description="本地化流程会在生成后展示。" />
          </n-card>

          <n-card title="历史记录" :bordered="false">
            <n-list v-if="history.length" hoverable clickable>
              <n-list-item v-for="item in history" :key="item.id" @click="selectHistory(item)">
                <n-thing :title="`${item.market} / ${item.language}`" :description="formatTime(item.createdAt)">
                  <template #header-extra>
                    <n-tag type="info" bordered>{{ item.strategy }}</n-tag>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
            <n-empty v-else description="暂无历史记录，本地化后会自动保存。" />
          </n-card>
        </n-space>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { getLocalizationHistory, processLocalization } from '../api/localization'
import { getEpisodeDetail } from '../api/episodes'
import { getScriptPolishHistory } from '../api/script'
import EpisodePicker from '../components/EpisodePicker.vue'
import ProjectPicker from '../components/ProjectPicker.vue'
import { useDictionaries } from '../composables/useDictionaries'
import { usePipelineStore } from '../stores/pipeline'
import type { ShortDramaEpisode } from '../types/episode'
import type { LocalizedSubtitle, LocalizationHistoryItem, LocalizationProcessRequest, LocalizationProcessResult } from '../types/localization'
import type { ShortDramaProject } from '../types/project'

const router = useRouter()
const route = useRoute()
const pipeline = usePipelineStore()
const { dictionaries, loadDictionaries } = useDictionaries()

const form = reactive<LocalizationProcessRequest>({
  market: '北美',
  language: 'en-US',
  strategy: '情绪强化',
  source_text: '',
})

const loading = ref(false)
const result = ref<LocalizationProcessResult | null>(null)
const history = ref<LocalizationHistoryItem[]>([])
const selectedProjectId = ref<number | null>(null)
const episodeId = ref<number | null>(null)
const episodeNo = ref<number | null>(null)
const selectedProject = ref<ShortDramaProject | null>(null)
const sourceTextTouched = ref(false)
const targetMarketTouched = ref(false)
const targetLanguageTouched = ref(false)
const sourceNotice = ref('未找到可用中文内容，请手动填写后再本地化。')
const sourceNoticeType = ref<'info' | 'warning' | 'success'>('warning')
const message = useMessage()

const strategyOptions = ['直译', '情绪强化', '文化适配', '广告转化优先'].map((item) => ({ label: item, value: item }))

type LooseRecord = Record<string, any>

function safeParseJson(value: unknown): unknown {
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

function pickText(...values: unknown[]) {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

function extractScriptText(record: unknown) {
  const item = record as LooseRecord
  const result = safeParseJson(item?.result) as LooseRecord
  const bilingual = (result?.bilingual || {}) as LooseRecord
  const zh = (bilingual?.zh || result?.zh || {}) as LooseRecord
  return pickText(
    zh.polishedScript,
    zh.optimizedScript,
    zh.script,
    result?.polishedScriptZh,
    result?.optimizedScriptZh,
    item?.polished_script_zh,
    item?.script_text,
    item?.original_script,
    item?.script,
  )
}

function extractHistorySourceText(item: LocalizationHistoryItem) {
  const raw = item as unknown as LooseRecord
  const resultData = (raw.result || {}) as LooseRecord
  const subtitleSource = Array.isArray(resultData.subtitles)
    ? resultData.subtitles.map((subtitle: LooseRecord) => subtitle.originalText).filter(Boolean).join('\n')
    : ''
  return pickText(raw.source_text, raw.sourceText, raw.original_text, resultData.sourceText, resultData.source_text, subtitleSource)
}

function setSourceNotice(messageText: string, type: 'info' | 'warning' | 'success' = 'info') {
  sourceNotice.value = messageText
  sourceNoticeType.value = type
}

function applySourceText(text: string, notice: string, type: 'info' | 'warning' | 'success' = 'success') {
  if (sourceTextTouched.value && form.source_text?.trim()) {
    setSourceNotice('当前本地化输入已手动编辑，未自动覆盖。', 'warning')
    return
  }
  form.source_text = text
  setSourceNotice(notice, type)
}

function applyProjectDefaults(project: ShortDramaProject | null) {
  if (!project) return
  if ((!targetMarketTouched.value || !form.market) && project.target_market) {
    form.market = project.target_market
  }
  const projectLanguage = (project as ShortDramaProject & { primary_language?: string }).primary_language || project.language
  if ((!targetLanguageTouched.value || !form.language) && projectLanguage) {
    form.language = projectLanguage
  }
}

async function autoFillLocalizationSource() {
  if (!selectedProjectId.value || !episodeId.value) return
  if (sourceTextTouched.value && form.source_text?.trim()) {
    setSourceNotice('当前本地化输入已手动编辑，未自动覆盖。', 'warning')
    return
  }

  try {
    const polishResponse = await getScriptPolishHistory({
      project_id: selectedProjectId.value,
      episode_id: episodeId.value,
      limit: 1,
    })
    const latestPolish = polishResponse.code === 0 ? polishResponse.data[0] : null
    const polishText = latestPolish ? extractScriptText(latestPolish) : ''
    if (polishText) {
      applySourceText(polishText, '已引用最近一次分集级剧本打磨中文结果作为本地化输入。', 'success')
      return
    }

    const episodeResponse = await getEpisodeDetail(episodeId.value)
    if (episodeResponse.code === 0 && episodeResponse.data?.summary) {
      const episode = episodeResponse.data
      applySourceText(`第 ${episode.episode_no} 集：${episode.title}\n${episode.summary}`, '未找到剧本打磨记录，已使用分集大纲作为本地化输入。', 'info')
      return
    }

    if (selectedProject.value?.description) {
      applySourceText(selectedProject.value.description, '未找到分集内容，已使用项目简介作为本地化输入。', 'warning')
      return
    }

    setSourceNotice('未找到可用中文内容，请手动填写后再本地化。', 'warning')
  } catch {
    setSourceNotice('未找到可用中文内容，请手动填写后再本地化。', 'warning')
  }
}

function handleSourceTextUpdate() {
  sourceTextTouched.value = true
  setSourceNotice('当前本地化输入已手动编辑，未自动覆盖。', 'warning')
}

function handleProjectChange(project: ShortDramaProject | null) {
  const previousProjectId = selectedProject.value?.id || null
  selectedProject.value = project
  applyProjectDefaults(project)
  if (previousProjectId && project?.id !== previousProjectId) {
    episodeId.value = null
    episodeNo.value = null
    if (!sourceTextTouched.value) form.source_text = ''
  }
  loadHistory()
  autoFillLocalizationSource()
}

function handleEpisodeChange(episode: ShortDramaEpisode | null) {
  episodeId.value = episode?.id || null
  episodeNo.value = episode?.episode_no || null
  loadHistory()
  autoFillLocalizationSource()
}

function statusTag(status: string) {
  if (status.includes('已')) return 'success'
  if (status.includes('待') || status.includes('未')) return 'warning'
  return 'default'
}

function workflowType(status: string) {
  if (status === '已完成') return 'success'
  if (status === '处理中') return 'info'
  return 'warning'
}

const columns = computed<DataTableColumns<LocalizedSubtitle>>(() => [
  { title: '#', key: 'index', width: 54 },
  { title: '开始', key: 'startTime', width: 82 },
  { title: '结束', key: 'endTime', width: 82 },
  { title: '中文原文', key: 'originalText', minWidth: 150 },
  { title: '直译', key: 'directTranslation', minWidth: 170 },
  { title: '本地化改写', key: 'localizedText', minWidth: 220 },
  { title: '配音', key: 'voiceStatus', width: 90, render: (row) => h(NTag, { type: statusTag(row.voiceStatus), bordered: false }, { default: () => row.voiceStatus }) },
  { title: '口型', key: 'lipSyncStatus', width: 90, render: (row) => h(NTag, { type: statusTag(row.lipSyncStatus), bordered: false }, { default: () => row.lipSyncStatus }) },
  { title: '字幕', key: 'subtitleStatus', width: 96, render: (row) => h(NTag, { type: statusTag(row.subtitleStatus), bordered: false }, { default: () => row.subtitleStatus }) },
])

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function selectHistory(item: LocalizationHistoryItem) {
  result.value = item.result
  sourceTextTouched.value = true
  targetMarketTouched.value = true
  targetLanguageTouched.value = true
  form.market = (item as unknown as LooseRecord).target_market || item.market
  form.language = (item as unknown as LooseRecord).target_language || item.language
  form.strategy = item.strategy
  form.source_text = extractHistorySourceText(item)
  setSourceNotice('已从历史记录恢复本地化输入和上下文。', 'info')
  // 点击历史时恢复链路 ID，旧数据没有这些字段时自动跳过。
  if (item.contentPlanId) pipeline.setContentPlanId(item.contentPlanId)
  if (item.scriptPolishId) pipeline.setScriptPolishId(item.scriptPolishId)
  if (item.storyboardId) pipeline.setStoryboardId(item.storyboardId)
  pipeline.setLocalizationId(item.recordId || item.id)
  if (item.project_id) selectedProjectId.value = item.project_id
  if (item.episode_id) episodeId.value = item.episode_id
  if (item.episode_no) episodeNo.value = item.episode_no
  message.success('已加载历史本地化结果')
}

async function loadHistory() {
  const response = await getLocalizationHistory({
    project_id: selectedProjectId.value || undefined,
    episode_id: episodeId.value || undefined,
    episode_no: episodeNo.value || undefined,
  })
  if (response.code === 0) history.value = response.data
}

function loadEpisodeQuery() {
  // 从分集列表进入时会携带 episodeId / episodeNo；没有这些参数时保持旧的独立本地化流程。
  const queryEpisodeId = Number(route.query.episodeId)
  const queryEpisodeNo = Number(route.query.episodeNo)
  episodeId.value = queryEpisodeId || null
  episodeNo.value = queryEpisodeNo || null
}

async function handleProcess() {
  if (!selectedProjectId.value) {
    message.warning('建议选择短剧项目，方便沉淀到完整生产链路。')
  }
  if (!episodeId.value) {
    message.warning('请选择具体分集，本地化结果需要沉淀到对应集数。')
    return
  }
  loading.value = true
  try {
    const response = await processLocalization({
      ...form,
      project_id: selectedProjectId.value,
      episode_id: episodeId.value,
      episode_no: episodeNo.value,
      contentPlanId: pipeline.contentPlanId,
      scriptPolishId: pipeline.scriptPolishId,
      storyboardId: pipeline.storyboardId,
    })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setLocalizationId(response.data.recordId)
      await loadHistory()
      message.success(selectedProjectId.value ? '已生成并归属到当前短剧项目。' : '本地化处理完成并保存')
    }
  } catch {
    message.error('本地化处理失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

function goWithContext(path: string) {
  const query = new URLSearchParams()
  if (selectedProjectId.value) query.set('projectId', String(selectedProjectId.value))
  if (episodeId.value) query.set('episodeId', String(episodeId.value))
  if (episodeNo.value) query.set('episodeNo', String(episodeNo.value))
  router.push(`${path}${query.toString() ? `?${query.toString()}` : ''}`)
}

onMounted(async () => {
  await loadDictionaries()
  loadEpisodeQuery()
  // 从项目详情页或分集列表进入时，ProjectPicker 会根据 projectId 加载并回显项目详情。
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) selectedProjectId.value = queryProjectId
  await loadHistory()
  await autoFillLocalizationSource()
})
</script>

<style scoped>
.module-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - 120px);
}

.config-card-content {
  position: relative;
}

.config-card-content > div:not(.project-bind-row) {
  position: absolute;
  top: -48px;
  right: 0;
}

.project-bind-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  align-items: stretch;
}

:global(.episode-picker) {
  height: 100%;
}

.project-select {
  flex: 1;
  margin-bottom: 0;
}

.source-input-item {
  margin-top: 14px;
}

.source-notice {
  margin-top: 4px;
}

.episode-context-card {
  margin-bottom: 14px;
  background: #f8fafc;
}

.episode-context-title {
  color: #111827;
  font-weight: 800;
}

.episode-context-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin: 8px 0 12px;
  color: #6b7280;
  font-size: 12px;
}

.result-card,
.workflow-card {
  min-height: 620px;
}

.localization-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fbfcff;
}

.result-title {
  color: #111827;
  font-size: 22px;
  font-weight: 800;
}

.result-copy {
  margin-top: 6px;
  color: #4b5563;
  line-height: 1.6;
}

.compare-card {
  margin-top: 16px;
  background: #fbfcff;
}

.compare-label {
  margin-bottom: 8px;
  color: #6b7280;
  font-size: 13px;
}

.compare-text {
  color: #374151;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.compare-text.strong {
  color: #1d4ed8;
  font-weight: 700;
}

.next-step-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.episode-back-btn {
  margin-left: 8px;
}
</style>
