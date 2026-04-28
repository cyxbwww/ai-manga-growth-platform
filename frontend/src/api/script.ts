import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { ScriptPolishHistoryItem, ScriptPolishRequest, ScriptPolishResult } from '../types/script'

// 剧本打磨：生成结果会在后端保存，并绑定可选的 project_id / episode_id 上下文。
export function polishScript(payload: ScriptPolishRequest) {
  return request.post<unknown, ApiResponse<ScriptPolishResult>>('/script/polish', payload)
}

export type ScriptPolishHistoryParams = {
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
}

// 获取最近 20 条剧本打磨历史记录，支持按项目或分集筛选。
export function getScriptPolishHistory(params: ScriptPolishHistoryParams = {}) {
  return request.get<unknown, ApiResponse<ScriptPolishHistoryItem[]>>('/script/polishes', { params })
}
