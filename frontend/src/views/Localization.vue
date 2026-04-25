<template>
  <div class="module-page">
    <n-card title="本地化配置" :bordered="false" class="config-card">
      <n-grid :cols="24" :x-gap="14" :y-gap="14" responsive="screen">
        <n-grid-item :span="5" :s-span="24">
          <n-form-item label="目标市场"><n-select v-model:value="form.market" :options="marketOptions" /></n-form-item>
        </n-grid-item>
        <n-grid-item :span="5" :s-span="24">
          <n-form-item label="目标语言"><n-select v-model:value="form.language" :options="languageOptions" /></n-form-item>
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
                <n-button type="primary" secondary @click="router.push('/ad-materials')">进入海外投放素材</n-button>
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
import { useRouter } from 'vue-router'
import { NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { getLocalizationHistory, processLocalization } from '../api/localization'
import { usePipelineStore } from '../stores/pipeline'
import type { LocalizedSubtitle, LocalizationHistoryItem, LocalizationProcessRequest, LocalizationProcessResult } from '../types/localization'

const router = useRouter()
const pipeline = usePipelineStore()

const form = reactive<LocalizationProcessRequest>({
  market: '北美',
  language: '英语',
  strategy: '情绪强化',
})

const loading = ref(false)
const result = ref<LocalizationProcessResult | null>(null)
const history = ref<LocalizationHistoryItem[]>([])
const message = useMessage()

const marketOptions = ['北美', '东南亚', '日本', '韩国', '中东'].map((item) => ({ label: item, value: item }))
const languageOptions = ['英语', '日语', '韩语', '泰语', '印尼语', '阿拉伯语'].map((item) => ({ label: item, value: item }))
const strategyOptions = ['直译', '情绪强化', '文化适配', '广告转化优先'].map((item) => ({ label: item, value: item }))

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
  // 点击历史时恢复链路 ID，旧数据没有这些字段时自动跳过。
  if (item.contentPlanId) pipeline.setContentPlanId(item.contentPlanId)
  if (item.scriptPolishId) pipeline.setScriptPolishId(item.scriptPolishId)
  if (item.storyboardId) pipeline.setStoryboardId(item.storyboardId)
  pipeline.setLocalizationId(item.recordId || item.id)
  message.success('已加载历史本地化结果')
}

async function loadHistory() {
  const response = await getLocalizationHistory()
  if (response.code === 0) history.value = response.data
}

async function handleProcess() {
  loading.value = true
  try {
    const response = await processLocalization({
      ...form,
      contentPlanId: pipeline.contentPlanId,
      scriptPolishId: pipeline.scriptPolishId,
      storyboardId: pipeline.storyboardId,
    })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setLocalizationId(response.data.recordId)
      await loadHistory()
      message.success('本地化处理完成并保存')
    }
  } catch {
    message.error('本地化处理失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.module-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - 120px);
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
</style>
