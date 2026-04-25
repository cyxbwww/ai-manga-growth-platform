<template>
  <div class="analytics-page">
    <n-spin :show="loading">
      <n-grid :cols="6" :x-gap="14" :y-gap="14" responsive="screen">
        <n-grid-item v-for="metric in metricCards" :key="metric.label" :s-span="24">
          <n-card :bordered="false" class="metric-card">
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value">{{ metric.value }}</div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen" class="chart-grid">
        <n-grid-item :span="12" :s-span="24">
          <n-card title="ROI 趋势" :bordered="false">
            <div ref="roiChartRef" class="chart"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item :span="12" :s-span="24">
          <n-card title="不同市场表现" :bordered="false">
            <div ref="marketChartRef" class="chart"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item :span="15" :s-span="24">
          <n-card title="不同素材点击率对比" :bordered="false">
            <div ref="creativeChartRef" class="chart"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item :span="9" :s-span="24">
          <n-card title="AI优化建议" :bordered="false" class="suggestion-card">
            <n-list v-if="overview">
              <n-list-item v-for="item in overview.suggestions" :key="item">
                <n-tag type="info" bordered>建议</n-tag>
                <span class="suggestion-text">{{ item }}</span>
              </n-list-item>
            </n-list>
            <n-empty v-else description="加载增长数据后展示 AI 优化建议。" />
          </n-card>
        </n-grid-item>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { useMessage } from 'naive-ui'
import { getAnalyticsOverview } from '../api/analytics'
import type { AnalyticsOverviewResult } from '../types/analytics'

const loading = ref(false)
const overview = ref<AnalyticsOverviewResult | null>(null)
const roiChartRef = ref<HTMLDivElement | null>(null)
const marketChartRef = ref<HTMLDivElement | null>(null)
const creativeChartRef = ref<HTMLDivElement | null>(null)
const message = useMessage()

const metricCards = computed(() => {
  const metrics = overview.value?.metrics
  if (!metrics) return []

  // 指标卡片：展示投放漏斗的核心经营指标。
  return [
    { label: '曝光量', value: metrics.impressions.toLocaleString() },
    { label: 'CTR', value: `${metrics.ctr}%` },
    { label: 'CVR', value: `${metrics.cvr}%` },
    { label: '广告消耗', value: `$${metrics.spend.toLocaleString()}` },
    { label: '收益', value: `$${metrics.revenue.toLocaleString()}` },
    { label: 'ROI', value: metrics.roi.toFixed(2) },
  ]
})

function renderCharts() {
  if (!overview.value || !roiChartRef.value || !marketChartRef.value || !creativeChartRef.value) return

  // ROI 趋势图：用于展示投放回收效率变化。
  echarts.init(roiChartRef.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 32, bottom: 32 },
    xAxis: { type: 'category', data: overview.value.roiTrend.map((item) => item.date) },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'ROI',
        type: 'line',
        smooth: true,
        data: overview.value.roiTrend.map((item) => item.roi),
        color: '#2563eb',
        areaStyle: { color: 'rgba(37, 99, 235, 0.12)' },
      },
    ],
  })

  // 市场表现图：对比不同国家和地区的收益与消耗。
  echarts.init(marketChartRef.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 44, right: 20, top: 42, bottom: 32 },
    xAxis: { type: 'category', data: overview.value.marketPerformance.map((item) => item.market) },
    yAxis: { type: 'value' },
    series: [
      {
        name: '收益',
        type: 'bar',
        data: overview.value.marketPerformance.map((item) => item.revenue),
        color: '#16a34a',
      },
      {
        name: '消耗',
        type: 'bar',
        data: overview.value.marketPerformance.map((item) => item.spend),
        color: '#f59e0b',
      },
    ],
  })

  // 素材 CTR 图：帮助判断哪类钩子和素材更值得放量。
  echarts.init(creativeChartRef.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 44, right: 20, top: 32, bottom: 32 },
    xAxis: { type: 'category', data: overview.value.creativeCtr.map((item) => item.creative) },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: 'CTR',
        type: 'bar',
        data: overview.value.creativeCtr.map((item) => item.ctr),
        color: '#7c3aed',
      },
    ],
  })
}

async function loadOverview() {
  loading.value = true
  try {
    const response = await getAnalyticsOverview()
    if (response.code === 0) {
      overview.value = response.data
      await nextTick()
      renderCharts()
    }
  } catch {
    message.error('增长分析数据加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<style scoped>
/* 增长分析页：用指标卡、图表和建议形成完整投放复盘视图。 */
.analytics-page {
  min-height: calc(100vh - 120px);
}

.metric-card {
  min-height: 112px;
  background: #ffffff;
}

.metric-label {
  color: #6b7280;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  color: #111827;
  font-size: 28px;
  font-weight: 800;
}

.chart-grid {
  margin-top: 18px;
}

.chart {
  width: 100%;
  height: 320px;
}

.suggestion-card {
  min-height: 374px;
}

.suggestion-text {
  margin-left: 10px;
  color: #374151;
  line-height: 1.7;
}
</style>
