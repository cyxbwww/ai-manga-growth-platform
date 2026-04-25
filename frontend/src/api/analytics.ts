import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { AnalyticsOverviewResult } from '../types/analytics'

// 获取增长分析总览：当前返回 mock 投放数据和 AI 优化建议。
export function getAnalyticsOverview() {
  return request.get<unknown, ApiResponse<AnalyticsOverviewResult>>('/analytics/overview')
}
