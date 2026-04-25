import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { ScriptPolishHistoryItem, ScriptPolishRequest, ScriptPolishResult } from '../types/script'

// 剧本打磨：生成结果会在后端保存，并绑定可选的 contentPlanId。
export function polishScript(payload: ScriptPolishRequest) {
  return request.post<unknown, ApiResponse<ScriptPolishResult>>('/script/polish', payload)
}

// 获取最近 20 条剧本打磨历史记录。
export function getScriptPolishHistory() {
  return request.get<unknown, ApiResponse<ScriptPolishHistoryItem[]>>('/script/polishes')
}
