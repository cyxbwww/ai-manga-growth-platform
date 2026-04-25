import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { StoryboardGenerateRequest, StoryboardGenerateResult, StoryboardHistoryItem } from '../types/storyboard'

// 生成 AI 分镜，支持携带上游链路 ID。
export function generateStoryboard(payload: StoryboardGenerateRequest) {
  return request.post<unknown, ApiResponse<StoryboardGenerateResult>>('/storyboard/generate', payload)
}

// 获取最近 20 条分镜历史记录。
export function getStoryboardHistory() {
  return request.get<unknown, ApiResponse<StoryboardHistoryItem[]>>('/storyboard/list')
}
