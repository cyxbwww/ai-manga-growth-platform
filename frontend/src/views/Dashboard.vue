<template>
  <div class="dashboard">
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <n-grid-item v-for="item in metricCards" :key="item.label">
        <n-card :title="item.label" :bordered="false">
          <div class="metric">{{ item.value }}</div>
          <div class="hint">{{ item.hint }}</div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card title="当前生产链路" :bordered="false">
      <div class="pipeline-header">
        <div>
          <div class="status-title">contentPlanId → scriptPolishId → storyboardId → localizationId → adMaterialId</div>
          <div class="status-copy">刷新页面后链路 ID 会从 localStorage 恢复，方便从任一模块继续生产。</div>
        </div>
        <n-space>
          <n-button secondary :disabled="!pipeline.contentPlanId" @click="loadPipelineDetail">查看链路详情</n-button>
          <n-button tertiary @click="resetPipeline">重置当前链路</n-button>
        </n-space>
      </div>

      <n-grid :cols="5" :x-gap="12" :y-gap="12" responsive="screen" class="pipeline-grid">
        <n-grid-item v-for="item in pipelineCards" :key="item.label">
          <div class="pipeline-step" :class="{ active: item.done }">
            <div class="step-label">{{ item.label }}</div>
            <n-tag :type="item.done ? 'success' : 'default'" bordered>{{ item.done ? '已生成' : '未生成' }}</n-tag>
            <div class="step-id">{{ item.id ? `ID: ${item.id}` : '等待生成' }}</div>
          </div>
        </n-grid-item>
      </n-grid>

      <n-alert v-if="pipelineDetailText" type="success" :bordered="false" class="pipeline-detail">
        {{ pipelineDetailText }}
      </n-alert>
    </n-card>

    <n-card class="chart-card" title="今日生成分布" :bordered="false">
      <div ref="chartRef" class="chart"></div>
    </n-card>

    <n-card title="AI 状态" :bordered="false">
      <div v-if="aiStatus" class="ai-status">
        <div>
          <div class="status-title">{{ aiStatus.enabled ? '真实 AI 已启用' : '当前为 mock/fallback 模式' }}</div>
          <div class="status-copy">
            Provider：{{ aiStatus.provider }} · 模型：{{ aiStatus.model }} · API Key：{{ aiStatus.hasApiKey ? '已配置' : '未配置' }}
          </div>
          <div class="status-copy">Base URL：{{ aiStatus.baseUrl }}</div>
        </div>
        <n-tag :type="aiStatus.enabled ? 'success' : 'warning'" bordered>
          {{ aiStatus.enabled ? 'DeepSeek' : 'Fallback' }}
        </n-tag>
      </div>
      <n-empty v-else description="AI 状态加载中" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import { getAiStatus } from '../api/ai'
import { getPipelineDetail } from '../api/pipeline'
import { usePipelineStore } from '../stores/pipeline'
import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { AiStatus } from '../types/ai'

type DashboardSummary = {
  todayContentPlans: number
  todayScriptPolishes: number
  todayStoryboards: number
  todayLocalizations: number
  todayAdMaterials: number
  totalRecords: number
}

const chartRef = ref<HTMLDivElement | null>(null)
const aiStatus = ref<AiStatus | null>(null)
const pipelineDetailText = ref('')
const pipeline = usePipelineStore()
const message = useMessage()

// Dashboard 数据来自 SQLite 真实统计，不再使用固定 mock 数字。
const summary = reactive<DashboardSummary>({
  todayContentPlans: 0,
  todayScriptPolishes: 0,
  todayStoryboards: 0,
  todayLocalizations: 0,
  todayAdMaterials: 0,
  totalRecords: 0,
})

const metricCards = computed(() => [
  { label: '今日内容策划', value: summary.todayContentPlans, hint: '内容策划生成次数' },
  { label: '今日剧本打磨', value: summary.todayScriptPolishes, hint: '剧本优化生成次数' },
  { label: '今日分镜制作', value: summary.todayStoryboards, hint: 'AI 分镜生成次数' },
  { label: '今日本地化', value: summary.todayLocalizations, hint: '多语种本地化次数' },
  { label: '今日广告素材', value: summary.todayAdMaterials, hint: '投放素材生成次数' },
  { label: '总生成记录', value: summary.totalRecords, hint: 'SQLite 中累计记录数' },
])

const pipelineCards = computed(() => [
  { label: '内容策划', id: pipeline.contentPlanId, done: Boolean(pipeline.contentPlanId) },
  { label: '剧本打磨', id: pipeline.scriptPolishId, done: Boolean(pipeline.scriptPolishId) },
  { label: '分镜制作', id: pipeline.storyboardId, done: Boolean(pipeline.storyboardId) },
  { label: '本地化', id: pipeline.localizationId, done: Boolean(pipeline.localizationId) },
  { label: '广告素材', id: pipeline.adMaterialId, done: Boolean(pipeline.adMaterialId) },
])

async function loadSummary() {
  const result = await request.get<unknown, ApiResponse<DashboardSummary>>('/dashboard/summary')
  if (result.code === 0) {
    Object.assign(summary, result.data)
  }
}

async function loadAiStatus() {
  const result = await getAiStatus()
  if (result.code === 0) {
    aiStatus.value = result.data
  }
}

async function loadPipelineDetail() {
  if (!pipeline.contentPlanId) return
  try {
    const result = await getPipelineDetail(pipeline.contentPlanId)
    const data = result.data
    pipelineDetailText.value = `链路详情：剧本打磨 ${data.scriptPolishes.length} 条，分镜 ${data.storyboards.length} 条，本地化 ${data.localizations.length} 条，广告素材 ${data.adMaterials.length} 条。`
  } catch {
    message.error('链路详情加载失败，请确认后端服务已启动')
  }
}

function resetPipeline() {
  pipeline.resetPipeline()
  pipelineDetailText.value = ''
  message.success('当前生产链路已重置')
}

function renderChart() {
  if (!chartRef.value) return

  // 图表展示今日各模块真实生成次数，便于演示持久化效果。
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 32, bottom: 28 },
    xAxis: {
      type: 'category',
      data: ['策划', '剧本', '分镜', '本地化', '广告'],
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '今日生成数',
        type: 'bar',
        data: [
          summary.todayContentPlans,
          summary.todayScriptPolishes,
          summary.todayStoryboards,
          summary.todayLocalizations,
          summary.todayAdMaterials,
        ],
        color: '#2563eb',
      },
    ],
  })
}

onMounted(async () => {
  await Promise.all([loadSummary(), loadAiStatus()])
  renderChart()
})
</script>

<style scoped>
/* 看板样式：聚焦真实统计、AI 状态和当前生产链路。 */
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.metric {
  color: #111827;
  font-size: 34px;
  font-weight: 800;
  line-height: 1.2;
}

.hint {
  margin-top: 8px;
  color: #6b7280;
  font-size: 13px;
}

.pipeline-header,
.ai-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.pipeline-grid {
  margin-top: 16px;
}

.pipeline-step {
  min-width: 0;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.pipeline-step.active {
  border-color: #18a058;
  background: #f0fdf4;
}

.step-label {
  margin-bottom: 10px;
  color: #111827;
  font-weight: 700;
}

.step-id {
  margin-top: 10px;
  color: #6b7280;
  font-size: 12px;
}

.pipeline-detail {
  margin-top: 14px;
}

.chart-card {
  min-height: 360px;
}

.chart {
  width: 100%;
  height: 300px;
}

.status-title {
  color: #111827;
  font-size: 18px;
  font-weight: 800;
}

.status-copy {
  margin-top: 6px;
  color: #4b5563;
  line-height: 1.6;
}
</style>
