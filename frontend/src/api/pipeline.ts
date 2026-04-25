import request from '../utils/request'
import type { ApiResponse } from '../types/common'

// 链路详情中的单条记录：后端会把 result_json 解析为 result 对象。
export type PipelineRecord = {
  id: number
  recordId?: number
  createdAt: string
  result: Record<string, any>
  [key: string]: any
}

// 当前内容策划下的完整生产链路。
export type PipelineDetail = {
  contentPlan: PipelineRecord | null
  scriptPolishes: PipelineRecord[]
  storyboards: PipelineRecord[]
  localizations: PipelineRecord[]
  adMaterials: PipelineRecord[]
}

export function getPipelineDetail(contentPlanId: number) {
  return request.get<unknown, ApiResponse<PipelineDetail>>(`/pipeline/${contentPlanId}`)
}
