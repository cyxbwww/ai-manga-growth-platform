<template>
  <div class="module-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="剧本拆镜输入" :bordered="false">
            <n-form :model="form" label-placement="top">
              <n-form-item label="所属短剧项目">
                <ProjectPicker
                  v-model="selectedProjectId"
                  placeholder="建议选择短剧项目，方便沉淀到完整生产链路"
                  @change="handleProjectChange"
                />
              </n-form-item>
              <n-form-item label="所属分集">
                <EpisodePicker
                  v-model="episodeId"
                  :project-id="selectedProjectId"
                  :episode-no="episodeNo"
                  placeholder="请选择要生成分镜的具体分集"
                  @change="handleEpisodeChange"
                />
              </n-form-item>
              <n-button v-if="selectedProjectId" tertiary size="small" class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}`)">
                返回项目详情
              </n-button>
              <n-button v-if="selectedProjectId" tertiary size="small" class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}/episodes`)">
                返回分集列表
              </n-button>
              <n-alert v-if="inputHydrateTip.message" :type="inputHydrateTip.type" :bordered="false" class="input-hydrate-tip">
                {{ inputHydrateTip.message }}
              </n-alert>
              <n-form-item label="剧本标题">
                <n-input v-model:value="form.title" @update:value="markInputTouched('title')" />
              </n-form-item>
              <n-form-item label="剧本文本">
                <n-input v-model:value="form.script" type="textarea" :autosize="{ minRows: 8, maxRows: 14 }" @update:value="markInputTouched('script')" />
              </n-form-item>
              <n-form-item label="画面风格">
                <n-select v-model:value="form.style" :options="styleOptions" />
              </n-form-item>
              <n-form-item label="分镜数量">
                <n-radio-group v-model:value="form.sceneCount">
                  <n-space>
                    <n-radio-button :value="4">4</n-radio-button>
                    <n-radio-button :value="6">6</n-radio-button>
                    <n-radio-button :value="8">8</n-radio-button>
                  </n-space>
                </n-radio-group>
              </n-form-item>
              <n-button type="primary" block size="large" :loading="loading" @click="handleGenerate">生成分镜</n-button>
            </n-form>
          </n-card>

          <n-card title="历史记录" :bordered="false">
            <n-list v-if="history.length" hoverable clickable>
              <n-list-item v-for="item in history" :key="item.id" @click="selectHistory(item)">
                <n-thing :title="item.title" :description="formatTime(item.createdAt)">
                  <template #header-extra>
                    <n-tag type="info" bordered>{{ item.sceneCount }}镜</n-tag>
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
          <n-card title="AI可生产化分镜" :bordered="false" class="result-card">
            <template #header-extra>
              <n-space>
                <n-radio-group v-if="hasBilingualScenes" v-model:value="displayLanguage" size="small">
                  <n-radio-button value="zh">中文</n-radio-button>
                  <n-radio-button value="target">{{ targetLanguage || '目标语言' }}</n-radio-button>
                </n-radio-group>
                <n-tag v-if="result" type="info" bordered>{{ result.style }}</n-tag>
                <n-button size="small" :disabled="!result" @click="exportJson">导出 JSON</n-button>
              </n-space>
            </template>

            <template v-if="result">
              <div class="result-summary">
                <div>
                  <div class="result-title">{{ result.storyboardTitle }}</div>
                  <div class="result-copy">将剧本拆成可直接进入图片生成、图生视频和角色一致性控制的生产数据。</div>
                </div>
                <n-statistic label="分镜数量" :value="result.scenes.length" />
              </div>

              <div class="storyboard-stack">
                <article v-for="scene in result.scenes" :key="getSceneDisplay(scene).sceneNo" class="story-card">
                  <div class="story-card-header">
                    <div class="scene-title-row">
                      <span class="scene-index">#{{ getSceneDisplay(scene).sceneNo }}</span>
                      <div class="scene-title story-content">{{ getSceneDisplay(scene).title }}</div>
                    </div>
                    <n-space align="center">
                      <n-tag type="default" bordered>待上传</n-tag>
                      <n-button size="small" secondary @click="goWithContext('/media-assets')">上传镜头素材</n-button>
                      <n-tag :type="statusType(getSceneDisplay(scene).status)" bordered>{{ getSceneDisplay(scene).status }}</n-tag>
                    </n-space>
                  </div>

                  <div class="story-card-body">
                    <div class="story-image">
                      <div>
                        <div class="image-placeholder-title">待生成画面</div>
                        <div class="image-placeholder-sub">{{ result.style }}</div>
                      </div>
                    </div>

                    <div class="story-info-panel">
                      <section class="story-section">
                        <div class="section-title">基础信息</div>
                        <div class="info-grid">
                          <div class="info-item">
                            <div class="info-label">标题</div>
                            <div class="info-text story-content">{{ getSceneDisplay(scene).title }}</div>
                          </div>
                          <div class="info-item compact">
                            <div class="info-label">时长</div>
                            <div class="info-text story-content">{{ getSceneDisplay(scene).duration }}</div>
                          </div>
                          <div class="info-item">
                            <div class="info-label">情绪</div>
                            <div class="info-text story-content">{{ getSceneDisplay(scene).emotion }}</div>
                          </div>
                          <div class="info-item compact">
                            <div class="info-label">状态</div>
                            <div class="info-text status-text">{{ getSceneDisplay(scene).status }}</div>
                          </div>
                        </div>
                      </section>

                      <n-divider />

                      <section class="story-section">
                        <div class="section-title">内容信息</div>
                        <div class="content-list">
                          <div class="info-item">
                            <div class="info-label">场景</div>
                            <div class="info-text story-content">{{ getSceneDisplay(scene).scene }}</div>
                          </div>
                          <div class="info-item">
                            <div class="info-label">动作</div>
                            <div class="info-text story-content">{{ getSceneDisplay(scene).characterAction }}</div>
                          </div>
                          <div class="info-item">
                            <div class="info-label">台词</div>
                            <div class="info-text story-content">{{ getSceneDisplay(scene).dialogue }}</div>
                          </div>
                        </div>
                      </section>

                      <n-divider />

                      <section class="story-section">
                        <div class="section-title">AI提示词</div>
                        <PromptBlock
                          title="图片提示词"
                          label="image"
                          :value="getSceneDisplay(scene).visualPrompt"
                          @copy="copyText(getSceneDisplay(scene).visualPrompt, '图片提示词已复制')"
                        />
                        <PromptBlock
                          title="视频提示词"
                          label="video"
                          :value="getSceneDisplay(scene).motionPrompt"
                          @copy="copyText(getSceneDisplay(scene).motionPrompt, '视频提示词已复制')"
                        />
                        <PromptBlock
                          title="一致性提示词"
                          label="consistency"
                          :value="getSceneDisplay(scene).consistencyPrompt"
                          @copy="copyText(getSceneDisplay(scene).consistencyPrompt, '一致性提示词已复制')"
                        />
                      </section>
                    </div>
                  </div>
                </article>
              </div>
              <div class="next-step-row">
                <n-button secondary @click="goWithContext('/media-assets')">上传分镜素材</n-button>
                <n-button type="primary" secondary @click="goWithContext('/localization')">进入多语种本地化</n-button>
              </div>
            </template>
            <n-empty v-else description="输入剧本后生成分镜，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NTag, useMessage } from 'naive-ui'
import { getEpisodeDetail } from '../api/episodes'
import { getScriptPolishHistory } from '../api/script'
import { generateStoryboard, getStoryboardHistory } from '../api/storyboard'
import EpisodePicker from '../components/EpisodePicker.vue'
import ProjectPicker from '../components/ProjectPicker.vue'
import { usePipelineStore } from '../stores/pipeline'
import type { ShortDramaEpisode } from '../types/episode'
import type { ShortDramaProject } from '../types/project'
import type { ScriptPolishHistoryItem } from '../types/script'
import type {
  StoryboardGenerateRequest,
  StoryboardGenerateResult,
  StoryboardHistoryItem,
  StoryboardScene,
  StoryboardSceneDisplay,
  StoryboardSceneText,
} from '../types/storyboard'

const EMPTY_TEXT = '暂无内容'

const form = reactive<StoryboardGenerateRequest>({
  title: '婚礼反击名场面',
  script: '婚礼现场，女主发现未婚夫和继妹联手夺走公司。她当众拿出股权文件，律师宣布她才是真正控股人。',
  style: '写实电影感',
  sceneCount: 6,
})

const loading = ref(false)
const result = ref<StoryboardGenerateResult | null>(null)
const history = ref<StoryboardHistoryItem[]>([])
const displayLanguage = ref<'zh' | 'target'>('zh')
const message = useMessage()
const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const selectedProjectId = ref<number | null>(null)
const episodeId = ref<number | null>(null)
const episodeNo = ref<number | null>(null)
const restoringHistory = ref(false)
const restoredHistoryContext = ref<{ projectId: number | null; episodeId: number | null } | null>(null)
const currentProject = ref<ShortDramaProject | null>(null)
const currentEpisode = ref<ShortDramaEpisode | null>(null)
const touchedInputs = reactive<Record<'title' | 'script', boolean>>({
  title: false,
  script: false,
})
const inputHydrateTip = reactive<{ type: 'success' | 'info' | 'warning' | 'error', message: string }>({
  type: 'info',
  message: '',
})

const styleOptions = ['写实电影感', '国风短剧', '赛博朋克', '日漫风', '欧美漫画'].map((item) => ({ label: item, value: item }))

function loadEpisodeQuery() {
  // 从分集列表进入时会携带 episodeId / episodeNo，这里只做读取和展示，不影响旧的独立生成流程。
  const queryEpisodeId = Number(route.query.episodeId)
  const queryEpisodeNo = Number(route.query.episodeNo)
  episodeId.value = queryEpisodeId || null
  episodeNo.value = queryEpisodeNo || null
}

const hasBilingualScenes = computed(() => Boolean(result.value?.scenes.some((scene) => scene.bilingual)))
const targetLanguage = computed(() => {
  const target = result.value?.scenes.find((scene) => scene.bilingual)?.bilingual?.target
  return typeof target === 'object' ? target.language || '目标语言' : '目标语言'
})

function markInputTouched(field: keyof typeof touchedInputs) {
  touchedInputs[field] = true
}

function canHydrateInput(field: keyof typeof touchedInputs, value?: string | null) {
  return !touchedInputs[field] || !String(value || '').trim()
}

function setInputHydrateTip(type: typeof inputHydrateTip.type, messageText: string) {
  inputHydrateTip.type = type
  inputHydrateTip.message = messageText
}

function handleProjectChange(project: ShortDramaProject | null) {
  currentProject.value = project
  if (restoringHistory.value) return
  if (restoredHistoryContext.value?.projectId && project?.id === restoredHistoryContext.value.projectId) return
  restoredHistoryContext.value = null
  loadHistory()
}

async function handleEpisodeChange(episode: ShortDramaEpisode | null) {
  episodeId.value = episode?.id || null
  episodeNo.value = episode?.episode_no || null
  currentEpisode.value = episode
  if (restoringHistory.value) return
  if (restoredHistoryContext.value?.episodeId && episode?.id === restoredHistoryContext.value.episodeId) return
  restoredHistoryContext.value = null
  if (episode) await hydrateStoryboardInput(episode)
  loadHistory()
}

const PromptBlock = defineComponent({
  props: {
    title: { type: String, required: true },
    label: { type: String, required: true },
    value: { type: String, required: true },
  },
  emits: ['copy'],
  setup(props, { emit }) {
    return () =>
      h('div', { class: 'prompt-box' }, [
        h('div', { class: 'prompt-toolbar' }, [
          // 提示词工具栏必须保持一行：类型标签、中文标题、复制按钮横向排列。
          h(
            NTag,
            { class: 'prompt-kind', size: 'small', type: 'info', bordered: false, style: { marginRight: '10px' } },
            { default: () => props.label },
          ),
          h('span', { class: 'prompt-name', style: { marginRight: '14px' } }, props.title),
          h(
            NButton,
            { class: 'prompt-copy', size: 'small', secondary: true, style: { marginLeft: '4px' }, onClick: () => emit('copy') },
            { default: () => '复制' },
          ),
        ]),
        h('div', { class: 'prompt-code story-content' }, props.value || EMPTY_TEXT),
      ])
  },
})

function readText(value: unknown): string {
  return typeof value === 'string' && value.trim() ? value : EMPTY_TEXT
}

function readMaybeText(value: unknown): string {
  return typeof value === 'string' && value.trim() ? value : ''
}

function parseMaybeJson(value: unknown): unknown {
  if (typeof value !== 'string') return value
  const text = value.trim()
  if (!text) return ''
  if (!text.startsWith('{') && !text.startsWith('[')) return text
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function readNestedText(source: unknown, paths: string[][]): string {
  const normalized = parseMaybeJson(source)
  for (const path of paths) {
    let cursor: unknown = normalized
    for (const key of path) {
      if (!cursor || typeof cursor !== 'object') {
        cursor = undefined
        break
      }
      cursor = (cursor as Record<string, unknown>)[key]
    }
    if (typeof cursor === 'string' && cursor.trim()) return cursor
  }
  return typeof normalized === 'string' && normalized.trim() ? normalized : ''
}

function readNestedValue(source: unknown, paths: string[][]): unknown {
  const normalized = parseMaybeJson(source)
  for (const path of paths) {
    let cursor: unknown = normalized
    for (const key of path) {
      if (!cursor || typeof cursor !== 'object') {
        cursor = undefined
        break
      }
      cursor = (cursor as Record<string, unknown>)[key]
    }
    if (cursor !== undefined && cursor !== null) return cursor
  }
  return undefined
}

function hasChineseText(text: string): boolean {
  return /[\u4e00-\u9fff]/.test(text)
}

function readTextCandidates(source: unknown, paths: string[][]) {
  const normalized = parseMaybeJson(source)
  if (typeof normalized === 'string' && normalized.trim()) return [normalized]
  const candidates: string[] = []
  for (const path of paths) {
    let cursor: unknown = normalized
    for (const key of path) {
      if (!cursor || typeof cursor !== 'object') {
        cursor = undefined
        break
      }
      cursor = (cursor as Record<string, unknown>)[key]
    }
    if (typeof cursor === 'string' && cursor.trim()) candidates.push(cursor)
  }
  return candidates
}

function pickChineseFirst(candidates: string[]) {
  return candidates.find(hasChineseText) || candidates[0] || ''
}

function extractPolishedScript(record: ScriptPolishHistoryItem) {
  const zhCandidates = readTextCandidates(record.result as unknown, [
    ['bilingual', 'zh', 'polishedScript'],
    ['bilingual', 'zh', 'optimizedScript'],
    ['bilingual', 'zh', 'script'],
    ['bilingual', 'zh', 'content'],
    ['zh', 'polishedScript'],
    ['zh', 'optimizedScript'],
    ['zh', 'script'],
    ['zh', 'content'],
    ['polishedScriptZh'],
    ['optimizedScriptZh'],
    ['chinesePolishedScript'],
    ['polished_script_zh'],
  ])
  const zhText = pickChineseFirst(zhCandidates)
  if (zhText && hasChineseText(zhText)) return { text: zhText, usedGenericFallback: false }

  const commonCandidates = [
    ...zhCandidates,
    ...readTextCandidates(record.result as unknown, [
      ['polishedScript'],
      ['optimizedScript'],
      ['script'],
      ['content'],
    ]),
    ...readTextCandidates(record as unknown, [
      ['polished_script'],
      ['script_text'],
      ['original_script'],
    ]),
  ].filter(Boolean)
  const commonText = pickChineseFirst(commonCandidates)
  return { text: commonText, usedGenericFallback: Boolean(commonText && !hasChineseText(commonText)) }
}

function extractPolishTitle(record: ScriptPolishHistoryItem, episode?: ShortDramaEpisode | null) {
  return formatEpisodeTitle(episode)
    || readNestedText(record.result as unknown, [['bilingual', 'zh', 'title'], ['zh', 'title']])
    || readNestedText(record as unknown, [['title'], ['script_title']])
    || readNestedText(record.result as unknown, [['title'], ['scriptTitle']])
    || formatEpisodeTitle(episode)
}

function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function extractStoryboardInputFromRecord(record: StoryboardHistoryItem) {
  const resultData = parseMaybeJson(record.result) as Record<string, unknown> | string
  const title = readNestedText(record as unknown, [['title'], ['script_title']])
    || readNestedText(resultData, [['title'], ['scriptTitle'], ['meta', 'title']])
    || form.title
  const script = readNestedText(record as unknown, [['script'], ['script_text'], ['original_script']])
    || readNestedText(resultData, [['script'], ['inputScript'], ['originalScript'], ['meta', 'scriptText']])
    || form.script
  const style = readNestedText(record as unknown, [['style'], ['visual_style']])
    || readNestedText(resultData, [['style'], ['visualStyle'], ['meta', 'style']])
    || form.style
  const resultScenes = (resultData as Record<string, unknown>)?.scenes
  const sceneCount = toNumber((record as unknown as Record<string, unknown>).scene_count)
    || toNumber((record as unknown as Record<string, unknown>).shot_count)
    || toNumber(record.sceneCount)
    || toNumber(readNestedValue(resultData, [['sceneCount'], ['shotCount']]))
    || (Array.isArray(resultScenes) ? resultScenes.length : null)
    || form.sceneCount
  return { title, script, style, sceneCount }
}

function syncStoryboardUrl(record: StoryboardHistoryItem) {
  const query: Record<string, string> = {}
  if (record.project_id) query.projectId = String(record.project_id)
  if (record.episode_id) query.episodeId = String(record.episode_id)
  if (record.episode_no) query.episodeNo = String(record.episode_no)
  router.replace({ path: route.path, query })
}

function formatEpisodeTitle(episode?: ShortDramaEpisode | null) {
  if (!episode) return ''
  const title = episode.title || ''
  return title.startsWith(`第 ${episode.episode_no} 集`) ? title : `第 ${episode.episode_no} 集：${title}`
}

function applyStoryboardInput(title: string, script: string) {
  const titleApplied = Boolean(title && canHydrateInput('title', form.title))
  const scriptApplied = Boolean(script && canHydrateInput('script', form.script))
  if (titleApplied) form.title = title
  if (scriptApplied) form.script = script
  return { titleApplied, scriptApplied }
}

async function loadEpisodeById(id: number) {
  if (currentEpisode.value?.id === id) return currentEpisode.value
  const response = await getEpisodeDetail(id)
  if (response.code === 0) {
    currentEpisode.value = response.data
    episodeNo.value = response.data.episode_no
    if (!selectedProjectId.value) selectedProjectId.value = response.data.project_id
    return response.data
  }
  return null
}

async function hydrateStoryboardInput(episode?: ShortDramaEpisode | null) {
  if (!selectedProjectId.value || !episodeId.value) return
  if (!canHydrateInput('title', form.title) && !canHydrateInput('script', form.script)) {
    setInputHydrateTip('warning', '当前剧本输入已手动编辑，未自动覆盖。')
    return
  }

  try {
    const resolvedEpisode = episode || await loadEpisodeById(episodeId.value)
    const historyResponse = await getScriptPolishHistory({
      project_id: selectedProjectId.value,
      episode_id: episodeId.value,
    })
    const polishRecord = historyResponse.code === 0 ? historyResponse.data[0] : undefined
    if (polishRecord) {
      const polishedScript = extractPolishedScript(polishRecord)
      const applied = applyStoryboardInput(extractPolishTitle(polishRecord, resolvedEpisode), polishedScript.text)
      if (polishRecord.recordId || polishRecord.id) pipeline.setScriptPolishId(polishRecord.recordId || polishRecord.id)
      if (!applied.titleApplied && !applied.scriptApplied) {
        setInputHydrateTip('warning', '当前剧本输入已手动编辑，未自动覆盖。')
      } else if (polishedScript.usedGenericFallback) {
        setInputHydrateTip('warning', '未找到中文剧本版本，已使用通用剧本字段，请确认是否需要手动调整。')
      } else {
        setInputHydrateTip('success', '已引用最近一次分集级剧本打磨结果。')
      }
      return
    }

    if (resolvedEpisode) {
      const applied = applyStoryboardInput(formatEpisodeTitle(resolvedEpisode), resolvedEpisode.summary || '')
      setInputHydrateTip(applied.titleApplied || applied.scriptApplied ? 'info' : 'warning', applied.titleApplied || applied.scriptApplied ? '未找到剧本打磨记录，已使用分集大纲作为分镜输入。' : '当前剧本输入已手动编辑，未自动覆盖。')
      return
    }

    const projectDescription = currentProject.value?.description || ''
    const applied = applyStoryboardInput(currentProject.value?.name || '', projectDescription)
    setInputHydrateTip(applied.titleApplied || applied.scriptApplied ? 'info' : 'warning', applied.titleApplied || applied.scriptApplied ? '未找到分集详情，已使用项目简介作为分镜输入。' : '当前剧本输入已手动编辑，未自动覆盖。')
  } catch {
    setInputHydrateTip('error', '分镜输入回填失败，请手动填写。')
  }
}

function normalizeSceneDisplay(scene: StoryboardScene, lang: 'zh' | 'target'): StoryboardSceneDisplay {
  // 新接口把实际内容放在 bilingual.zh / bilingual.target，旧历史数据则仍在顶层字段。
  const bilingualValue = lang === 'zh' ? scene.bilingual?.zh : scene.bilingual?.target
  const bilingualObject: StoryboardSceneText = typeof bilingualValue === 'object' && bilingualValue !== null ? bilingualValue : {}
  const bilingualSceneText = typeof bilingualValue === 'string' ? bilingualValue : ''

  // 字段读取优先级：当前语言 bilingual 对象 > bilingual 字符串作为场景描述 > 旧顶层字段 > 兜底文案。
  const sceneNo = scene.sceneNo ?? scene.sceneNumber ?? 0
  const title = readText(bilingualObject.title ?? scene.title ?? (sceneNo ? `分镜 ${sceneNo}` : '分镜'))
  const sceneText = readText(bilingualObject.scene ?? bilingualSceneText ?? scene.scene)

  return {
    sceneNo,
    title,
    scene: sceneText,
    characterAction: readText(bilingualObject.characterAction ?? scene.characterAction),
    dialogue: readText(bilingualObject.dialogue ?? scene.dialogue),
    emotion: readText(bilingualObject.emotion ?? scene.emotion),
    visualPrompt: readText(bilingualObject.visualPrompt ?? scene.visualPrompt),
    motionPrompt: readText(bilingualObject.motionPrompt ?? scene.motionPrompt),
    consistencyPrompt: readText(bilingualObject.consistencyPrompt ?? scene.consistencyPrompt),
    duration: readText(scene.duration),
    status: readMaybeText(scene.status) || '待生成',
  }
}

function getSceneDisplay(scene: StoryboardScene): StoryboardSceneDisplay {
  // 模板统一调用该方法，确保生成结果和历史记录都走同一套兼容逻辑。
  return normalizeSceneDisplay(scene, displayLanguage.value)
}

function statusType(status: string) {
  if (status.includes('已生成')) return 'success'
  if (status.includes('优化')) return 'warning'
  return 'default'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

async function selectHistory(item: StoryboardHistoryItem) {
  restoringHistory.value = true
  try {
    const input = extractStoryboardInputFromRecord(item)
    result.value = item.result
    selectedProjectId.value = item.project_id || null
    episodeId.value = item.episode_id || null
    episodeNo.value = item.episode_no || null
    restoredHistoryContext.value = { projectId: selectedProjectId.value, episodeId: episodeId.value }
    currentEpisode.value = null
    touchedInputs.title = false
    touchedInputs.script = false
    form.title = input.title
    form.script = input.script
    form.style = input.style
    form.sceneCount = input.sceneCount
    if (item.contentPlanId) pipeline.setContentPlanId(item.contentPlanId)
    if (item.scriptPolishId) pipeline.setScriptPolishId(item.scriptPolishId)
    pipeline.setStoryboardId(item.recordId || item.id)
    displayLanguage.value = 'zh'
    syncStoryboardUrl(item)
    await nextTick()
    setInputHydrateTip(
      item.project_id || item.episode_id ? 'success' : 'info',
      item.project_id || item.episode_id ? '已恢复该分镜任务的项目、分集和输入内容。' : '已加载历史分镜结果，该记录未绑定项目或分集。',
    )
  } finally {
    restoringHistory.value = false
  }
}

async function copyText(text: string, successText: string) {
  try {
    await navigator.clipboard.writeText(text || EMPTY_TEXT)
    message.success(successText)
  } catch {
    message.error('复制失败，请手动选择文本复制')
  }
}

function exportJson() {
  if (!result.value) return
  const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${result.value.storyboardTitle}.json`
  link.click()
  URL.revokeObjectURL(url)
  message.success('分镜 JSON 已导出')
}

async function loadHistory() {
  const response = await getStoryboardHistory({
    project_id: selectedProjectId.value || undefined,
    episode_id: episodeId.value || undefined,
    episode_no: episodeNo.value || undefined,
  })
  if (response.code === 0) history.value = response.data
}

function goWithContext(path: string) {
  const query = new URLSearchParams()
  if (selectedProjectId.value) query.set('projectId', String(selectedProjectId.value))
  if (episodeId.value) query.set('episodeId', String(episodeId.value))
  if (episodeNo.value) query.set('episodeNo', String(episodeNo.value))
  router.push(`${path}${query.toString() ? `?${query.toString()}` : ''}`)
}

function showStoryboardGenerateError(error: unknown) {
  const responseData = (error as { response?: { data?: { detail?: unknown } } })?.response?.data
  const detail = responseData?.detail
  if (detail && typeof detail === 'object' && (detail as { code?: string }).code === 'STORYBOARD_LLM_JSON_PARSE_FAILED') {
    const reason = (detail as { reason?: string }).reason
    const suffix = import.meta.env.DEV && reason ? `原因：${reason}` : ''
    message.error(`AI分镜结果解析失败，模型返回内容不是合法 JSON。请重试，或适当缩短剧本文本后再生成。${suffix}`)
    return
  }
  if (detail && typeof detail === 'object' && (detail as { code?: string }).code === 'STORYBOARD_DUPLICATE_CONTENT') {
    const reasons = Array.isArray((detail as { reasons?: unknown }).reasons)
      ? ((detail as { reasons: string[] }).reasons).filter(Boolean)
      : []
    const suffix = reasons.length ? `原因：${reasons.join('、')}` : ''
    message.error(`AI分镜结果重复度过高，请补充剧本细节、减少分镜数量或重新生成。${suffix}`)
    return
  }
  message.error('分镜生成失败，请确认后端服务已启动')
}

async function handleGenerate() {
  if (!form.title.trim() || !form.script.trim()) {
    message.warning('请填写剧本标题和剧本文本')
    return
  }
  if (!selectedProjectId.value) {
    message.warning('建议选择短剧项目，方便沉淀到完整生产链路。')
  }
  if (!episodeId.value) {
    message.warning('请选择具体分集，AI分镜结果需要沉淀到对应集数。')
    return
  }
  loading.value = true
  try {
    const response = await generateStoryboard({
      ...form,
      project_id: selectedProjectId.value,
      episode_id: episodeId.value,
      episode_no: episodeNo.value,
      contentPlanId: pipeline.contentPlanId,
      scriptPolishId: pipeline.scriptPolishId,
    })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setStoryboardId(response.data.recordId)
      displayLanguage.value = 'zh'
      await loadHistory()
      message.success(selectedProjectId.value ? '已生成并归属到当前短剧项目。' : '分镜已生成并保存')
    }
  } catch (error) {
    showStoryboardGenerateError(error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loadEpisodeQuery()
  // 从项目详情页或分集列表进入时，ProjectPicker 会根据 projectId 加载并回显项目详情。
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) selectedProjectId.value = queryProjectId
  if (selectedProjectId.value && episodeId.value) await hydrateStoryboardInput()
  await loadHistory()
})
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.result-card {
  min-height: 720px;
}

.input-hydrate-tip {
  margin-bottom: 14px;
}

.result-card :deep(.n-grid-item) {
  min-width: 0;
}

.result-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-width: 0;
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

.storyboard-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.story-card {
  min-width: 0;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.story-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.scene-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.scene-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  color: #ffffff;
  border-radius: 999px;
  background: #18a058;
  font-size: 12px;
  font-weight: 800;
  line-height: 20px;
}

.scene-title {
  min-width: 0;
  color: #111827;
  font-size: 16px;
  font-weight: 800;
}

.story-card-body {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 0;
}

.story-image {
  position: relative;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 180px;
  height: 240px;
  padding: 14px;
  color: #ffffff;
  border: 1px solid rgba(37, 99, 235, 0.25);
  border-radius: 8px;
  background: linear-gradient(135deg, #111827, #2563eb);
  text-align: center;
}

.image-placeholder-title {
  font-size: 15px;
  font-weight: 800;
}

.image-placeholder-sub {
  margin-top: 8px;
  color: #dbeafe;
  font-size: 12px;
}

.story-info-panel {
  flex: 1;
  min-width: 0;
}

.story-section {
  min-width: 0;
}

.section-title {
  margin-bottom: 10px;
  color: #111827;
  font-size: 14px;
  font-weight: 800;
}

.info-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  gap: 12px;
}

.content-list {
  display: grid;
  gap: 10px;
}

.info-item {
  min-width: 0;
}

.info-label {
  margin-bottom: 6px;
  color: #6b7280;
  font-size: 12px;
}

.info-text {
  min-height: 36px;
  padding: 8px 12px;
  color: #374151;
  border-radius: 6px;
  background: #f7f8fa;
  line-height: 1.6;
}

.status-text {
  color: #374151;
  background: #f7f8fa;
}

.story-content {
  white-space: normal;
  word-break: break-word;
  overflow-wrap: break-word;
}

.project-back-btn {
  margin: -6px 8px 14px 0;
}

.episode-context-card {
  margin: -4px 0 14px;
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

.prompt-box {
  min-width: 0;
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f5f7fa;
}

.prompt-box:last-child {
  margin-bottom: 0;
}

:deep(.prompt-toolbar) {
  margin-bottom: 8px;
}

.prompt-name {
  min-width: 0;
  color: #374151;
  font-weight: 700;
  white-space: nowrap;
  line-height: 24px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.prompt-kind,
.prompt-copy,
.prompt-toolbar :deep(.n-button),
.prompt-toolbar :deep(.n-tag) {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.prompt-kind {
  margin-right: 4px;
}

.prompt-name {
  margin-right: 8px;
}

.prompt-copy {
  margin-left: 4px;
}

.prompt-code {
  max-height: 132px;
  margin: 0;
  overflow-y: auto;
  color: #111827;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.next-step-row {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .story-card-body {
    flex-direction: column;
  }

  .story-image {
    width: 100%;
    max-width: 220px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
