import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { AiStatus } from '../types/ai'

// 获取后端 AI 配置状态：用于 Dashboard 展示 DeepSeek 是否启用。
export function getAiStatus() {
  return request.get<unknown, ApiResponse<AiStatus>>('/ai/status')
}
