<template>
  <div class="module-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="投放素材输入" :bordered="false">
            <n-alert v-if="hasPipelineContext" type="success" :bordered="false" class="pipeline-tip">
              已绑定当前生产链路，生成时会自动携带上游内容 ID。
            </n-alert>
            <n-alert v-else type="info" :bordered="false" class="pipeline-tip">
              当前页面可独立使用，也可从上一环节进入以自动带入内容。
            </n-alert>

            <n-form :model="form" label-placement="top">
              <n-form-item label="所属短剧项目">
                <ProjectPicker
                  v-model="selectedProjectId"
                  placeholder="建议选择短剧项目，方便沉淀到完整生产链路"
                  @change="handleProjectChange"
                />
              </n-form-item>
              <n-form-item label="所属分集（可选）">
                <EpisodePicker
                  v-model="episodeId"
                  :project-id="selectedProjectId"
                  :episode-no="episodeNo"
                  placeholder="可选择某一集生成分集级广告素材"
                  @change="handleEpisodeChange"
                />
              </n-form-item>
              <n-button v-if="selectedProjectId" secondary block class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}`)">
                返回项目详情
              </n-button>
              <n-button v-if="selectedProjectId" secondary block class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}/episodes`)">
                返回分集列表
              </n-button>
              <n-alert type="info" :bordered="false" class="pipeline-tip">
                未选择分集时，素材将作为项目级广告素材保存；选择分集后可围绕单集爆点生成投放素材。
              </n-alert>
              <n-form-item label="项目名称"><n-input v-model:value="form.projectName" /></n-form-item>
              <n-form-item label="目标市场">
                <n-select
                  v-model:value="form.market"
                  filterable
                  label-field="label"
                  value-field="value"
                  placeholder="请选择目标市场"
                  :options="dictionaries.markets"
                />
              </n-form-item>
              <n-form-item label="投放平台"><n-select v-model:value="form.platform" :options="platformOptions" /></n-form-item>
              <n-form-item label="内容类型"><n-select v-model:value="form.contentType" :options="contentTypeOptions" /></n-form-item>
              <n-button type="primary" block size="large" :loading="loading" @click="handleGenerate">生成广告素材</n-button>
            </n-form>
          </n-card>

          <n-card title="历史记录" :bordered="false">
            <n-list v-if="history.length" hoverable clickable>
              <n-list-item v-for="item in history" :key="item.id" @click="selectHistory(item)">
                <n-thing :title="item.projectName" :description="formatTime(item.createdAt)">
                  <template #header-extra>
                    <n-tag type="info" bordered>{{ item.platform }}</n-tag>
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
          <n-card title="海外投放素材包" :bordered="false" class="result-card">
            <template #header-extra>
              <n-space align="center">
                <n-radio-group v-if="result?.bilingual" v-model:value="displayLanguage" size="small">
                  <n-radio-button value="zh">中文</n-radio-button>
                  <n-radio-button value="target">{{ result.bilingual.target.language || '目标语言' }}</n-radio-button>
                </n-radio-group>
                <n-tag v-if="result" type="info" bordered>{{ result.platform }} / {{ result.market }}</n-tag>
              </n-space>
            </template>

            <template v-if="result">
              <div class="summary-block">
                <div class="result-title">{{ result.projectName }}</div>
                <div class="result-copy">围绕 {{ result.contentType }} 生成适合短视频平台测试的标题、钩子和转化文案。</div>
              </div>

              <n-grid :cols="3" :x-gap="14" :y-gap="14" responsive="screen">
                <n-grid-item v-for="item in adCopies" :key="item.id">
                  <n-card size="small" class="creative-card" :class="{ recommended: item.recommended }">
                    <template #header>
                      <div class="card-title-row">
                        <span>素材 {{ item.id }}</span>
                        <n-tag v-if="item.recommended" type="success" bordered>推荐</n-tag>
                      </div>
                    </template>
                    <div class="field-label">广告标题</div>
                    <p class="creative-title">{{ item.title }}</p>
                    <div class="field-label">前 3 秒钩子</div>
                    <p>{{ item.hook }}</p>
                    <div class="field-label">投放文案</div>
                    <p>{{ item.copy }}</p>
                    <n-space>
                      <n-button size="small" secondary @click="copyAdCopy(item.copy)">复制广告文案</n-button>
                      <n-button size="small" tertiary @click="markRecommended(item.id)">标记推荐</n-button>
                    </n-space>
                  </n-card>
                </n-grid-item>
              </n-grid>

              <n-grid :cols="2" :x-gap="14" :y-gap="14" responsive="screen" class="section-grid">
                <n-grid-item>
                  <n-card size="small" title="CTA 文案" class="info-card">
                    <n-space><n-tag v-for="item in adView.cta" :key="item" type="success" bordered>{{ item }}</n-tag></n-space>
                  </n-card>
                </n-grid-item>
                <n-grid-item>
                  <n-card size="small" title="封面图提示词" class="info-card">
                    <p>{{ adView.coverPrompt }}</p>
                    <n-button size="small" secondary @click="copyAdCopy(adView.coverPrompt)">复制封面提示词</n-button>
                  </n-card>
                </n-grid-item>
              </n-grid>

              <n-card size="small" title="A/B 测试建议" class="info-card">
                <n-list><n-list-item v-for="item in adView.abTestSuggestions" :key="item">{{ item }}</n-list-item></n-list>
              </n-card>
            </template>
            <n-empty v-else description="填写左侧信息后生成素材，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { generateAds, getAdMaterialHistory } from '../api/ads'
import { getPipelineDetail } from '../api/pipeline'
import EpisodePicker from '../components/EpisodePicker.vue'
import ProjectPicker from '../components/ProjectPicker.vue'
import { useDictionaries } from '../composables/useDictionaries'
import { usePipelineStore } from '../stores/pipeline'
import type { AdCopyItem, AdMaterialHistoryItem, AdsBilingualFields, AdsGenerateRequest, AdsGenerateResult } from '../types/ads'
import type { ShortDramaEpisode } from '../types/episode'
import type { ShortDramaProject } from '../types/project'

const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const { dictionaries, loadDictionaries } = useDictionaries()
const form = reactive<AdsGenerateRequest>({
  projectName: '逆袭千金海外版',
  market: '北美',
  platform: 'TikTok',
  contentType: '爽文逆袭',
})

const loading = ref(false)
const result = ref<AdsGenerateResult | null>(null)
const history = ref<AdMaterialHistoryItem[]>([])
const displayLanguage = ref<'zh' | 'target'>('zh')
const selectedProjectId = ref<number | null>(null)
const episodeId = ref<number | null>(null)
const episodeNo = ref<number | null>(null)
const message = useMessage()

const platformOptions = ['TikTok', 'Instagram Reels', 'YouTube Shorts'].map((item) => ({ label: item, value: item }))
const contentTypeOptions = ['情感反转', '爽文逆袭', '悬疑钩子', '家庭冲突'].map((item) => ({ label: item, value: item }))

const hasPipelineContext = computed(() => Boolean(pipeline.contentPlanId || pipeline.scriptPolishId || pipeline.storyboardId || pipeline.localizationId))

function handleProjectChange(_project: ShortDramaProject | null) {
  loadHistory()
}

function handleEpisodeChange(episode: ShortDramaEpisode | null) {
  episodeId.value = episode?.id || null
  episodeNo.value = episode?.episode_no || null
  loadHistory()
}

const adView = computed<AdsBilingualFields>(() => {
  // 兼容旧历史数据：没有 bilingual 时继续展示顶层字段。
  if (!result.value?.bilingual) {
    return {
      titles: result.value?.titles || [],
      hooks: result.value?.hooks || [],
      copies: result.value?.copies.map((item) => item.copy) || [],
      cta: result.value?.cta || [],
      coverPrompt: result.value?.coverPrompt || '',
      abTestSuggestions: result.value?.abTestSuggestions || [],
    }
  }
  return displayLanguage.value === 'target' ? result.value.bilingual.target : result.value.bilingual.zh
})

const adCopies = computed<AdCopyItem[]>(() => {
  if (!result.value) return []
  return adView.value.copies.map((copy, index) => ({
    id: index + 1,
    title: adView.value.titles[index] || `素材 ${index + 1}`,
    hook: adView.value.hooks[index] || '',
    copy,
    recommended: result.value?.copies[index]?.recommended ?? index === 0,
  }))
})

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function selectHistory(item: AdMaterialHistoryItem) {
  result.value = item.result
  displayLanguage.value = 'zh'
  // 历史记录点击后尽量恢复整条生产链路。
  if (item.contentPlanId) pipeline.setContentPlanId(item.contentPlanId)
  if (item.scriptPolishId) pipeline.setScriptPolishId(item.scriptPolishId)
  if (item.storyboardId) pipeline.setStoryboardId(item.storyboardId)
  if (item.localizationId) pipeline.setLocalizationId(item.localizationId)
  pipeline.setAdMaterialId(item.recordId || item.id)
  if (item.project_id) selectedProjectId.value = item.project_id
  message.success('已加载历史广告素材')
}

async function copyAdCopy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    message.success('内容已复制')
  } catch {
    message.error('复制失败，请手动选择文本复制')
  }
}

function markRecommended(id: number) {
  if (!result.value) return
  // 推荐标记仅用于当前前端演示，不回写数据库。
  result.value.copies = result.value.copies.map((item: AdCopyItem) => ({ ...item, recommended: item.id === id }))
  message.success(`素材 ${id} 已标记为推荐`)
}

async function loadHistory() {
  const response = await getAdMaterialHistory({
    project_id: selectedProjectId.value || undefined,
    episode_id: episodeId.value || undefined,
    episode_no: episodeNo.value || undefined,
  })
  if (response.code === 0) history.value = response.data
}

function loadEpisodeQuery() {
  // 广告素材可选绑定分集；没有 episode 参数时仍作为项目级素材生成。
  const queryEpisodeId = Number(route.query.episodeId)
  const queryEpisodeNo = Number(route.query.episodeNo)
  episodeId.value = queryEpisodeId || null
  episodeNo.value = queryEpisodeNo || null
}

async function hydrateFromPipeline() {
  if (!pipeline.contentPlanId) return
  try {
    const response = await getPipelineDetail(pipeline.contentPlanId)
    const contentPlanRecord = response.data.contentPlan
    const contentPlan = contentPlanRecord?.result
    if (contentPlan) {
      form.projectName = contentPlan.title || form.projectName
      form.market = contentPlanRecord?.market || form.market
      form.contentType = contentPlanRecord?.genre || form.contentType
    }
  } catch {
    // 自动带入失败不阻塞页面独立使用。
  }
}

async function handleGenerate() {
  if (!form.projectName.trim()) {
    message.warning('请填写项目名称')
    return
  }
  if (!selectedProjectId.value) {
    message.warning('建议选择短剧项目，方便沉淀到完整生产链路。')
  }
  if (!episodeId.value) {
    message.warning('未选择分集，本次将作为项目级广告素材保存。')
  }
  loading.value = true
  try {
    const response = await generateAds({
      ...form,
      project_id: selectedProjectId.value,
      episode_id: episodeId.value,
      episode_no: episodeNo.value,
      contentPlanId: pipeline.contentPlanId,
      scriptPolishId: pipeline.scriptPolishId,
      storyboardId: pipeline.storyboardId,
      localizationId: pipeline.localizationId,
    })
    if (response.code === 0) {
      result.value = response.data
      displayLanguage.value = 'zh'
      if (response.data.recordId) pipeline.setAdMaterialId(response.data.recordId)
      await loadHistory()
      message.success(selectedProjectId.value ? '已生成并归属到当前短剧项目。' : '广告素材已生成并保存')
    }
  } catch {
    message.error('广告素材生成失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDictionaries()
  loadEpisodeQuery()
  // 从项目详情页或分集列表进入时，ProjectPicker 会根据 projectId 加载并回显项目详情。
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) selectedProjectId.value = queryProjectId
  await Promise.all([loadHistory(), hydrateFromPipeline()])
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
  margin-bottom: 14px;
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

.result-card {
  min-height: 680px;
}

.summary-block {
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

.creative-card,
.info-card {
  min-width: 0;
  background: #fbfcff;
}

.creative-card.recommended {
  border-color: #22c55e;
  box-shadow: 0 8px 24px rgba(34, 197, 94, 0.12);
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.field-label {
  margin-top: 10px;
  color: #6b7280;
  font-size: 12px;
}

.creative-title {
  color: #111827;
  font-weight: 800;
}

p {
  margin: 6px 0 10px;
  color: #374151;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.section-grid {
  margin-top: 14px;
  margin-bottom: 14px;
}
</style>
