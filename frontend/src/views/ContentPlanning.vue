<template>
  <div class="module-page content-planning-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="策划输入" :bordered="false">
            <n-form :model="form" label-placement="top">
              <n-form-item label="项目名称">
                <n-input v-model:value="form.projectName" placeholder="例如：逆袭千金的北美爆款短剧" />
              </n-form-item>
              <n-form-item label="短剧题材">
                <n-select v-model:value="form.genre" :options="genreOptions" />
              </n-form-item>
              <n-form-item label="目标市场">
                <n-select v-model:value="form.market" :options="marketOptions" />
              </n-form-item>
              <n-form-item label="目标语言">
                <n-select v-model:value="form.language" :options="languageOptions" />
              </n-form-item>
              <n-form-item label="视频时长">
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
                    <n-tag type="info" bordered>{{ item.market }}</n-tag>
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
                <n-radio-button value="target">{{ result.bilingual.target.language || '目标语言' }}</n-radio-button>
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
                <n-button type="primary" secondary @click="router.push('/script-polish')">进入剧本打磨</n-button>
              </div>
            </template>
            <n-empty v-else description="填写左侧信息后生成策划方案，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTag, useMessage } from 'naive-ui'
import { createContentPlan, getContentPlanHistory } from '../api/content'
import { usePipelineStore } from '../stores/pipeline'
import type { ContentPlanBilingualFields, ContentPlanHistoryItem, ContentPlanRequest, ContentPlanResult } from '../types/content'

const form = reactive<ContentPlanRequest>({
  projectName: '逆袭千金的北美爆款短剧',
  genre: '爽文逆袭',
  market: '北美',
  language: '英文',
  duration: '60秒',
  sellingPoint: '女主被家族抛弃后用商业能力反击，前3秒需要强冲突，结尾留下复仇反转。',
})

const loading = ref(false)
const result = ref<ContentPlanResult | null>(null)
const history = ref<ContentPlanHistoryItem[]>([])
const displayLanguage = ref<'zh' | 'target'>('zh')
const message = useMessage()
const router = useRouter()
const pipeline = usePipelineStore()

const genreOptions = ['都市情感', '家庭亲情', '悬疑反转', '爽文逆袭', '海外霸总'].map((item) => ({ label: item, value: item }))
const marketOptions = ['北美', '东南亚', '日本', '韩国', '中东'].map((item) => ({ label: item, value: item }))
const languageOptions = ['英文', '日文', '韩文', '泰文', '印尼文'].map((item) => ({ label: item, value: item }))

const contentView = computed<ContentPlanBilingualFields>(() => {
  // 旧历史数据没有 bilingual 时直接使用顶层字段，确保向后兼容。
  if (!result.value?.bilingual) return result.value as ContentPlanResult
  return displayLanguage.value === 'target' ? result.value.bilingual.target : result.value.bilingual.zh
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

function selectHistory(item: ContentPlanHistoryItem) {
  result.value = item.result
  pipeline.setContentPlanId(item.recordId || item.id)
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

  loading.value = true
  try {
    const response = await createContentPlan({ ...form })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setContentPlanId(response.data.recordId)
      displayLanguage.value = 'zh'
      await loadHistory()
      message.success('策划方案已生成并保存')
    }
  } catch {
    message.error('策划方案生成失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.result-card {
  min-height: 620px;
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
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
