<template>
  <div class="module-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="剧本输入" :bordered="false">
            <!-- 项目级定位说明：弱化旧 contentPlanId 链路，强调整部短剧的规划打磨能力。 -->
            <n-alert type="info" :bordered="false" class="pipeline-tip">
              {{ workspaceDescription }}
            </n-alert>
            <n-alert v-if="selectedProjectId" type="success" :bordered="false" class="pipeline-tip">
              当前结果将归属到所选短剧项目。
            </n-alert>
            <n-alert v-else type="warning" :bordered="false" class="pipeline-tip">
              建议选择短剧项目，方便沉淀到项目级规划链路。
            </n-alert>

            <n-form :model="form" label-placement="top">
              <n-form-item label="所属短剧项目">
                <ProjectPicker
                  v-model="selectedProjectId"
                  placeholder="建议选择短剧项目，方便沉淀到项目级规划链路"
                  @change="handleProjectChange"
                />
              </n-form-item>
              <n-button v-if="selectedProjectId" tertiary size="small" class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}`)">
                返回项目详情
              </n-button>
              <n-form-item label="所属分集">
                <EpisodePicker
                  v-model="selectedEpisodeId"
                  :project-id="selectedProjectId"
                  :episode-no="selectedEpisodeNo"
                  placeholder="可选：选择分集后切换为分集级剧本打磨"
                  clearable
                  @change="handleEpisodeChange"
                />
              </n-form-item>
              <n-alert v-if="contentPlanTip.message" :type="contentPlanTip.type" :bordered="false" class="pipeline-tip">
                {{ contentPlanTip.message }}
              </n-alert>
              <n-form-item label="剧本标题">
                <n-input
                  v-model:value="form.title"
                  placeholder="例如：她在婚礼当天醒悟"
                  @update:value="markFieldTouched('title')"
                />
              </n-form-item>
              <n-form-item label="原始剧本文本">
                <n-input
                  v-model:value="form.script"
                  type="textarea"
                  :autosize="{ minRows: 10, maxRows: 16 }"
                  @update:value="markFieldTouched('script')"
                />
              </n-form-item>
              <n-form-item label="打磨方向">
                <n-checkbox-group v-model:value="form.directions">
                  <n-space vertical>
                    <n-checkbox value="强化前三秒钩子">强化前三秒钩子</n-checkbox>
                    <n-checkbox value="增强冲突">增强冲突</n-checkbox>
                    <n-checkbox value="加强反转">加强反转</n-checkbox>
                    <n-checkbox value="提升情绪张力">提升情绪张力</n-checkbox>
                    <n-checkbox value="适配海外表达">适配海外表达</n-checkbox>
                  </n-space>
                </n-checkbox-group>
              </n-form-item>
              <n-button type="primary" block size="large" :loading="loading" @click="handlePolish">开始打磨</n-button>
            </n-form>
          </n-card>

          <n-card title="历史记录" :bordered="false">
            <n-list v-if="history.length" hoverable clickable>
              <n-list-item v-for="item in history" :key="item.id" @click="selectHistory(item)">
                <n-thing :title="item.title" :description="formatTime(item.createdAt)">
                  <template #header-extra>
                    <n-space size="small">
                      <n-tag type="success" bordered>{{ getLabel('languages', item.language || item.target_language) }}</n-tag>
                      <n-tag type="warning" bordered>{{ item.result.score }}分</n-tag>
                    </n-space>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
            <n-empty v-else description="暂无历史记录，打磨后会自动保存。" />
          </n-card>
        </n-space>
      </n-grid-item>

      <n-grid-item :span="16" :s-span="24">
        <n-spin :show="loading">
          <n-card :title="workspaceTitle" :bordered="false" class="result-card">
            <template #header-extra>
              <n-space align="center">
                <n-radio-group v-if="result?.bilingual" v-model:value="displayLanguage" size="small">
                  <n-radio-button value="zh">中文</n-radio-button>
                  <n-radio-button value="target">{{ result.bilingual.target.language || '目标语言' }}</n-radio-button>
                </n-radio-group>
                <n-tag type="info" bordered>辅助内容精品化</n-tag>
              </n-space>
            </template>

            <template v-if="result">
              <section class="score-panel">
                <div class="score-main">
                  <n-progress type="circle" :percentage="result.score" :height="94" status="success" />
                  <div>
                    <div class="score-title">剧本综合评分</div>
                    <div class="score-copy">AI 从节奏、冲突、反转和情绪张力四个维度辅助判断剧本可投放性。</div>
                  </div>
                </div>
                <div class="score-dimensions">
                  <div v-for="item in dimensionScores" :key="item.label" class="dimension-item">
                    <div class="dimension-head">
                      <span>{{ item.label }}</span>
                      <strong>{{ item.value }}</strong>
                    </div>
                    <n-progress type="line" :percentage="item.value" :height="8" :show-indicator="false" status="success" />
                  </div>
                </div>
              </section>

              <n-grid :cols="2" :x-gap="16" :y-gap="16" responsive="screen">
                <n-grid-item>
                  <n-card size="small" title="问题诊断" class="inner-card">
                    <div class="diagnostic-list">
                      <div v-for="item in diagnosticCards" :key="item.type" class="diagnostic-card">
                        <n-tag type="warning" size="small" bordered>{{ item.type }}</n-tag>
                        <div class="diagnostic-row">
                          <span>问题</span>
                          <p>{{ item.problem }}</p>
                        </div>
                        <div class="diagnostic-row">
                          <span>建议</span>
                          <p>{{ item.suggestion }}</p>
                        </div>
                        <div class="diagnostic-row example">
                          <span>示例</span>
                          <p>{{ item.example }}</p>
                        </div>
                      </div>
                    </div>
                  </n-card>
                </n-grid-item>

                <n-grid-item>
                  <n-card size="small" title="优化建议" class="inner-card">
                    <div class="tip-groups">
                      <div v-for="group in tipGroups" :key="group.label" class="tip-group">
                        <n-tag :type="group.type" size="small" bordered>{{ group.label }}</n-tag>
                        <ul>
                          <li v-for="tip in group.items" :key="tip">{{ tip }}</li>
                        </ul>
                      </div>
                    </div>
                  </n-card>
                </n-grid-item>
              </n-grid>

              <n-card size="small" title="优化后剧本片段" class="inner-card">
                <template #header-extra>
                  <n-space>
                    <n-button size="small" secondary @click="copyPolishedScript">复制优化剧本</n-button>
                    <n-button size="small" tertiary @click="replaceOriginalScript">一键替换原剧本</n-button>
                  </n-space>
                </template>
                <pre class="script-output">{{ scriptView.polishedScript }}</pre>
              </n-card>

              <n-card size="small" title="海外本地化改写示例" class="inner-card">
                <div class="localization-note">
                  <strong>直译：</strong>语言翻译，保留原句含义。
                  <strong>本地化表达：</strong>符合目标市场表达习惯，更适合短剧投放。
                </div>
                <n-table :bordered="false" :single-line="false" class="localization-table">
                  <thead>
                    <tr><th>原句</th><th>直译</th><th>本地化表达</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in result.localizedRewrite" :key="item.original">
                      <td>{{ item.original }}</td>
                      <td>{{ item.directTranslation }}</td>
                      <td><div class="localized-highlight">{{ item.localizedVersion }}</div></td>
                    </tr>
                  </tbody>
                </n-table>
              </n-card>

              <div class="next-step-row">
                <n-button type="primary" secondary @click="goStoryboard">进入分镜制作</n-button>
              </div>
            </template>
            <n-empty v-else description="输入剧本并选择打磨方向，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { getContentPlanHistory } from '../api/content'
import { getEpisodeDetail } from '../api/episodes'
import { getPipelineDetail } from '../api/pipeline'
import { getScriptPolishHistory, polishScript } from '../api/script'
import EpisodePicker from '../components/EpisodePicker.vue'
import ProjectPicker from '../components/ProjectPicker.vue'
import { useDictionaries } from '../composables/useDictionaries'
import { usePipelineStore } from '../stores/pipeline'
import type { ContentPlanHistoryItem } from '../types/content'
import type { ScriptPolishBilingualFields, ScriptPolishHistoryItem, ScriptPolishRequest, ScriptPolishResult } from '../types/script'
import type { ShortDramaProject } from '../types/project'
import type { ShortDramaEpisode } from '../types/episode'

type ProjectChangePayload = ShortDramaProject & {
  primary_language?: string
}

const defaultForm: ScriptPolishRequest = {
  title: '她在婚礼当天醒悟',
  script: '女主站在婚礼现场，发现未婚夫和继妹早已联手骗走她的公司。她没有哭，只是拿出一份合同，说真正的控股人是她。全场安静，未婚夫慌了。',
  directions: ['强化前三秒钩子', '增强冲突', '加强反转', '适配海外表达'],
}

const form = reactive<ScriptPolishRequest>(defaultForm)

const loading = ref(false)
const result = ref<ScriptPolishResult | null>(null)
const history = ref<ScriptPolishHistoryItem[]>([])
const displayLanguage = ref<'zh' | 'target'>('zh')
const message = useMessage()
const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const { getLabel, loadDictionaries } = useDictionaries()
const selectedProjectId = ref<number | null>(null)
const selectedEpisodeId = ref<number | null>(null)
const selectedEpisodeNo = ref<number | null>(null)
const currentProject = ref<ProjectChangePayload | null>(null)
const currentEpisode = ref<ShortDramaEpisode | null>(null)
const selectedLanguage = ref('en-US')
const contentPlanTip = reactive<{ type: 'success' | 'info' | 'warning' | 'error', message: string }>({
  type: 'info',
  message: '',
})
const touchedFields = reactive<Record<'title' | 'script', boolean>>({
  title: false,
  script: false,
})

const scriptView = computed<ScriptPolishBilingualFields>(() => {
  // 旧历史数据没有 bilingual 时，继续使用顶层中文字段展示。
  if (!result.value?.bilingual) {
    return {
      polishedScript: result.value?.polishedScript || '',
      optimizationTips: result.value?.optimizationTips || [],
    }
  }
  return displayLanguage.value === 'target' ? result.value.bilingual.target : result.value.bilingual.zh
})

const isEpisodeMode = computed(() => Boolean(selectedEpisodeId.value))

const workspaceTitle = computed(() => {
  if (!isEpisodeMode.value) return '项目级剧本打磨工作台'
  const no = selectedEpisodeNo.value || currentEpisode.value?.episode_no || route.query.episodeNo
  return no ? `第 ${no} 集剧本打磨工作台` : '分集级剧本打磨工作台'
})

const workspaceDescription = computed(() =>
  isEpisodeMode.value
    ? '用于优化该集剧情、台词、转折、结尾悬念和短剧节奏。'
    : '用于整部短剧的大纲、核心冲突、人物关系、整体节奏和前三秒钩子优化。',
)

const dimensionScores = computed(() => {
  const base = result.value?.score || 0
  return [
    { label: '节奏', value: clampScore(base + 4) },
    { label: '冲突', value: clampScore(base + 2) },
    { label: '反转', value: clampScore(base - 3) },
    { label: '情绪张力', value: clampScore(base + 1) },
  ]
})

const diagnosticExamples = [
  '示例：开场直接给出“合同被公开”或“婚礼现场背叛”，让观众在前三秒理解冲突。',
  '示例：用对手的公开羞辱动作替代解释性旁白，让主角反击更有爽感。',
  '示例：把“我会证明自己”改成“今晚，我拿回他们偷走的一切”。',
]

const diagnosticCards = computed(() =>
  (result.value?.diagnostics || []).map((item, index) => ({
    ...item,
    example: diagnosticExamples[index % diagnosticExamples.length],
  })),
)

const tipGroups = computed(() => {
  const tips = scriptView.value.optimizationTips
  return [
    { label: '剧情优化', type: 'warning' as const, items: tips.filter((_, index) => index % 3 === 0) },
    { label: '表达优化', type: 'info' as const, items: tips.filter((_, index) => index % 3 === 1) },
    { label: '投放优化', type: 'success' as const, items: tips.filter((_, index) => index % 3 === 2) },
  ].map((group) => ({
    ...group,
    items: group.items.length ? group.items : ['当前维度暂无独立建议，可结合其它建议继续优化。'],
  }))
})

function clampScore(value: number) {
  return Math.max(0, Math.min(100, value))
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function markFieldTouched(field: keyof typeof touchedFields) {
  touchedFields[field] = true
}

function shouldHydrateField(field: keyof typeof touchedFields, currentValue?: string | null) {
  return !touchedFields[field] || !String(currentValue || '').trim()
}

function hydrateField(field: keyof ScriptPolishRequest, value?: string | null) {
  if (!value) return
  if (field === 'title' && shouldHydrateField('title', form.title)) form.title = value
  if (field === 'script' && shouldHydrateField('script', form.script)) form.script = value
}

function setContentPlanTip(type: typeof contentPlanTip.type, message: string) {
  contentPlanTip.type = type
  contentPlanTip.message = message
}

function formatPlanValue(value: unknown) {
  if (Array.isArray(value)) return value.join('\n')
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

function readPlanField(result: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = result[key]
    if (value !== undefined && value !== null && formatPlanValue(value).trim()) return formatPlanValue(value)
  }
  return ''
}

function appendSection(sections: string[], title: string, content?: string | null) {
  const text = (content || '').trim()
  if (text) sections.push(`【${title}】\n${text}`)
}

function buildScriptInputFromContentPlan(plan: ContentPlanHistoryItem) {
  const rawResult = plan.result
  if (typeof rawResult === 'string') {
    return `${rawResult}\n\n请基于以上内容进行剧本打磨。`
  }

  const result = rawResult && typeof rawResult === 'object' ? rawResult as Record<string, unknown> : {}
  const sections: string[] = []
  appendSection(sections, '项目名称', plan.projectName || readPlanField(result, ['title']))
  appendSection(sections, '故事定位', readPlanField(result, ['positioning', 'storyPositioning', '故事定位']))
  appendSection(sections, '目标用户', readPlanField(result, ['targetAudience', '目标用户']))
  appendSection(sections, '核心冲突', readPlanField(result, ['coreConflict', '核心冲突']))
  appendSection(sections, '情绪钩子', readPlanField(result, ['emotionHook', 'emotionalHook', '情绪钩子']))
  appendSection(sections, '前三秒开场建议', readPlanField(result, ['openingHook', 'threeSecondHook', '3秒开头建议', '前三秒开场建议']))
  appendSection(sections, '爽点/泪点/反转点', readPlanField(result, ['highlights', 'sellingPoints', '爽点', '泪点', '反转点']))
  appendSection(sections, '投放平台', readPlanField(result, ['platforms', '适合投放平台']))
  appendSection(sections, 'AI策划建议', readPlanField(result, ['suggestions', 'aiSuggestions', 'AI策划建议']))
  appendSection(sections, '剧本打磨要求', '请基于以上内容，优化短剧的开场钩子、冲突节奏、人物动机、台词表达和每集结尾悬念。')
  return sections.join('\n\n')
}

async function getLatestContentPlan(projectId?: number | null) {
  if (!projectId) return undefined
  const response = await getContentPlanHistory({ project_id: projectId, limit: 1 })
  return response.code === 0 ? response.data[0] : undefined
}

async function buildEpisodeScriptInput(episode: ShortDramaEpisode) {
  const project = currentProject.value
  let projectContext = project?.description || ''
  try {
    const latestPlan = await getLatestContentPlan(episode.project_id || selectedProjectId.value)
    if (latestPlan) {
      projectContext = buildScriptInputFromContentPlan(latestPlan)
      if (latestPlan.recordId || latestPlan.id) pipeline.setContentPlanId(latestPlan.recordId || latestPlan.id)
    }
  } catch {
    projectContext = project?.description || ''
  }

  const episodeTitle = episode.title?.startsWith(`第 ${episode.episode_no} 集`)
    ? episode.title
    : `第 ${episode.episode_no} 集：${episode.title}`

  const sections = [
    `【所属项目】\n${project?.name || form.title || ''}`,
    `【当前分集】\n${episodeTitle}`,
    `【分集剧情摘要】\n${episode.summary || episode.title || ''}`,
  ]
  if (projectContext.trim()) sections.push(`【项目背景补充】\n${projectContext.trim()}`)
  sections.push('【本集打磨要求】\n请重点优化本集前三秒开场、关键冲突、人物台词、情绪爆点和结尾悬念。')
  return sections.join('\n\n')
}

async function hydrateScriptFromEpisode(episode: ShortDramaEpisode) {
  currentEpisode.value = episode
  selectedEpisodeId.value = episode.id
  selectedEpisodeNo.value = episode.episode_no
  if (!selectedProjectId.value || selectedProjectId.value !== episode.project_id) {
    selectedProjectId.value = episode.project_id
  }
  hydrateField('title', episode.title || currentProject.value?.name)

  if (touchedFields.script) {
    setContentPlanTip('warning', '已选择分集，当前原始文本已手动编辑，未覆盖。')
    return
  }
  form.script = await buildEpisodeScriptInput(episode)
  setContentPlanTip('success', '已引用当前分集大纲。')
}

async function hydrateScriptFromLatestContentPlan(project: ProjectChangePayload) {
  if (touchedFields.script) {
    setContentPlanTip('warning', '已选择项目，当前原始文本已手动编辑，未覆盖。')
    return
  }

  try {
    const latestPlan = await getLatestContentPlan(project.id)
    if (latestPlan) {
      form.script = buildScriptInputFromContentPlan(latestPlan)
      if (latestPlan.recordId || latestPlan.id) pipeline.setContentPlanId(latestPlan.recordId || latestPlan.id)
      setContentPlanTip('success', '已引用该项目最近一次内容策划结果。')
      return
    }

    form.script = project.description || ''
    setContentPlanTip('info', '未找到内容策划结果，已使用项目简介作为剧本打磨输入。')
  } catch {
    form.script = project.description || ''
    setContentPlanTip('warning', '内容策划查询失败，已使用项目简介兜底。')
  }
}

async function handleProjectChange(project: ProjectChangePayload | null) {
  if (!project) {
    currentProject.value = null
    currentEpisode.value = null
    selectedEpisodeId.value = null
    selectedEpisodeNo.value = null
    selectedLanguage.value = 'en-US'
    contentPlanTip.message = ''
    return
  }
  const projectChanged = Boolean(currentProject.value?.id && currentProject.value.id !== project.id)
  currentProject.value = project
  selectedLanguage.value = project.primary_language || project.language || 'en-US'
  if (projectChanged && (!selectedEpisodeId.value || currentEpisode.value?.project_id !== project.id)) {
    currentEpisode.value = null
    selectedEpisodeId.value = null
    selectedEpisodeNo.value = null
    await nextTick()
  }
  // 选择项目后仅同步未手动编辑过的输入，避免覆盖编剧已经补充的标题和剧本文本。
  hydrateField('title', project.name)
  if (!selectedEpisodeId.value) await hydrateScriptFromLatestContentPlan(project)
  message.success('已同步短剧项目基础信息。')
}

async function handleEpisodeChange(episode: ShortDramaEpisode | null) {
  if (!episode) {
    currentEpisode.value = null
    selectedEpisodeId.value = null
    selectedEpisodeNo.value = null
    if (currentProject.value) {
      setContentPlanTip('info', '已清空分集，当前切换为项目级剧本打磨。')
    }
    return
  }
  await hydrateScriptFromEpisode(episode)
}

async function hydrateEpisodeById(episodeId: number) {
  try {
    const response = await getEpisodeDetail(episodeId)
    if (response.code === 0 && response.data) {
      await hydrateScriptFromEpisode(response.data)
    }
  } catch {
    setContentPlanTip('warning', '分集详情加载失败，请重新选择分集。')
  }
}

async function selectHistory(item: ScriptPolishHistoryItem) {
  result.value = item.result
  form.title = item.title || form.title
  form.script = item.script || form.script
  form.directions = item.directions || form.directions
  touchedFields.title = true
  touchedFields.script = true
  selectedLanguage.value = item.language || item.target_language || selectedLanguage.value
  selectedProjectId.value = item.project_id || null
  if (item.episode_id) {
    selectedEpisodeId.value = item.episode_id
    selectedEpisodeNo.value = item.episode_no || null
    await hydrateEpisodeById(item.episode_id)
  } else {
    currentEpisode.value = null
    selectedEpisodeId.value = null
    selectedEpisodeNo.value = null
  }
  if (item.contentPlanId) pipeline.setContentPlanId(item.contentPlanId)
  pipeline.setScriptPolishId(item.recordId || item.id)
  displayLanguage.value = 'zh'
  message.success('已加载历史打磨结果')
}

async function copyPolishedScript() {
  try {
    await navigator.clipboard.writeText(scriptView.value.polishedScript)
    message.success('优化剧本已复制')
  } catch {
    message.error('复制失败，请手动选择文本复制')
  }
}

function replaceOriginalScript() {
  form.script = scriptView.value.polishedScript
  markFieldTouched('script')
  message.success('已用优化剧本替换原剧本')
}

function goStoryboard() {
  if (isEpisodeMode.value && selectedProjectId.value && selectedEpisodeId.value) {
    router.push(`/storyboard?projectId=${selectedProjectId.value}&episodeId=${selectedEpisodeId.value}&episodeNo=${selectedEpisodeNo.value || ''}`)
    return
  }
  router.push('/storyboard')
}

async function loadHistory() {
  const response = await getScriptPolishHistory()
  if (response.code === 0) {
    history.value = response.data
  }
}

async function hydrateFromPipeline() {
  if (!pipeline.contentPlanId) return
  try {
    const response = await getPipelineDetail(pipeline.contentPlanId)
    const contentPlan = response.data.contentPlan
    const plan = contentPlan?.result
    if (plan) {
      form.title = plan.title || form.title
      form.script = `项目标题：${plan.title || form.title}\n故事定位：${plan.positioning || ''}\n核心冲突：${plan.coreConflict || ''}\n3秒开头：${plan.openingHook || ''}\n\n请基于以上策划生成可用于短视频短剧的剧本草稿。`
    }
  } catch {
    // 自动带入失败不影响页面独立使用。
  }
}

async function handlePolish() {
  if (!form.title.trim() || !form.script.trim()) {
    message.warning('请填写剧本标题和原始剧本文本')
    return
  }
  if (!selectedProjectId.value) {
    message.warning('建议选择短剧项目，方便沉淀到项目级规划链路。')
  }

  loading.value = true
  try {
    const payload: ScriptPolishRequest = {
      ...form,
      project_id: selectedProjectId.value,
      language: selectedLanguage.value,
      contentPlanId: pipeline.contentPlanId,
    }
    if (isEpisodeMode.value && selectedEpisodeId.value) {
      payload.episode_id = selectedEpisodeId.value
      payload.episode_no = selectedEpisodeNo.value || currentEpisode.value?.episode_no || null
    }
    const response = await polishScript({
      ...payload,
    })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setScriptPolishId(response.data.recordId)
      displayLanguage.value = 'zh'
      await loadHistory()
      message.success(isEpisodeMode.value ? '分集级剧本打磨完成，该集已进入 AI 分镜阶段。' : (selectedProjectId.value ? '项目级剧本打磨结果已归属到当前短剧项目。' : '项目级剧本打磨完成并保存'))
    }
  } catch {
    message.error('剧本打磨失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDictionaries()
  // 从项目详情页进入时，先写入 projectId，ProjectPicker 会负责加载并回显项目信息。
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) {
    selectedProjectId.value = queryProjectId
    hydrateFromPipeline()
  }
  const queryEpisodeId = Number(route.query.episodeId)
  const queryEpisodeNo = Number(route.query.episodeNo)
  if (queryEpisodeId) {
    selectedEpisodeId.value = queryEpisodeId
    selectedEpisodeNo.value = queryEpisodeNo || null
    await hydrateEpisodeById(queryEpisodeId)
  }
  await Promise.all([loadHistory()])
})
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.pipeline-tip {
  margin-bottom: 14px;
}

.project-back-btn {
  margin: -6px 0 14px;
}

.result-card {
  min-height: 680px;
}

.result-card :deep(.n-grid-item),
.result-card :deep(.n-list-item),
.result-card :deep(td) {
  min-width: 0;
  white-space: normal !important;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.score-panel {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  margin-bottom: 18px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fbfcff;
}

.score-main {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.score-title {
  color: #111827;
  font-size: 20px;
  font-weight: 800;
}

.score-copy {
  margin-top: 8px;
  color: #4b5563;
  line-height: 1.7;
}

.score-dimensions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-content: center;
}

.dimension-item {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #eef2f7;
  border-radius: 8px;
  background: #ffffff;
}

.dimension-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #374151;
}

.inner-card {
  min-width: 0;
  margin-bottom: 16px;
  background: #fbfcff;
}

.diagnostic-list,
.tip-groups {
  display: grid;
  gap: 12px;
}

.diagnostic-card,
.tip-group {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
}

.diagnostic-row {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 10px;
  margin-top: 8px;
}

.diagnostic-row span {
  color: #6b7280;
  font-size: 12px;
}

.diagnostic-row p {
  margin: 0;
  color: #374151;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.diagnostic-row.example p {
  padding: 8px 10px;
  border-radius: 6px;
  background: #fff7ed;
  color: #9a3412;
}

.tip-group ul {
  margin: 10px 0 0;
  padding-left: 18px;
}

.tip-group li {
  margin-bottom: 8px;
  color: #374151;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.script-output {
  max-height: 280px;
  margin: 0;
  overflow-y: auto;
  color: #374151;
  font-family: "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.localization-note {
  margin-bottom: 12px;
  padding: 10px 12px;
  color: #374151;
  border-radius: 8px;
  background: #f7f8fa;
  line-height: 1.7;
}

.localization-note strong {
  color: #111827;
}

.localized-highlight {
  padding: 8px 10px;
  border-radius: 6px;
  background: #ecfdf5;
  color: #047857;
  font-weight: 700;
  line-height: 1.7;
}

.next-step-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .score-panel {
    grid-template-columns: 1fr;
  }

  .score-dimensions {
    grid-template-columns: 1fr;
  }
}
</style>
