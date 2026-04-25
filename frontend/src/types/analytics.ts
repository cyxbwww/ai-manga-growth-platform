// 指标卡片数据：用于展示投放效果总览。
export type AnalyticsMetric = {
  impressions: number
  ctr: number
  cvr: number
  spend: number
  revenue: number
  roi: number
}

// 趋势数据点：用于 ROI 折线图。
export type RoiTrendItem = {
  date: string
  roi: number
}

// 市场表现：用于不同市场表现柱状图。
export type MarketPerformanceItem = {
  market: string
  revenue: number
  spend: number
  roi: number
}

// 素材点击率：用于不同素材 CTR 对比图。
export type CreativeCtrItem = {
  creative: string
  ctr: number
}

// 增长分析总览返回：包含指标、图表数据和 AI 优化建议。
export type AnalyticsOverviewResult = {
  metrics: AnalyticsMetric
  roiTrend: RoiTrendItem[]
  marketPerformance: MarketPerformanceItem[]
  creativeCtr: CreativeCtrItem[]
  suggestions: string[]
}
