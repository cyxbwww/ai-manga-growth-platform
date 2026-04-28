import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { ContentPlanHistoryItem, ContentPlanListParams, ContentPlanRequest, ContentPlanResult } from '../types/content'

// 创建内容策划方案：当前调用后端 mock 接口，后续可替换真实 AI 服务。
export function createContentPlan(payload: ContentPlanRequest) {
  return request.post<unknown, ApiResponse<ContentPlanResult>>('/content/plan', payload)
}

// 获取内容策划历史记录：用于页面刷新后继续查看最近生成结果。
export function getContentPlanHistory(params?: ContentPlanListParams) {
  return request.get<unknown, ApiResponse<ContentPlanHistoryItem[]>>('/content/plans', { params })
}
