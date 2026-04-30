import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type {
  LocalizationHistoryItem,
  LocalizationProcessRequest,
  LocalizationProcessResult,
} from '../types/localization'

// 执行多语种本地化：必须把当前项目、分集和输入剧本文本一起传给后端。
export function processLocalization(payload: LocalizationProcessRequest) {
  return request.post<unknown, ApiResponse<LocalizationProcessResult>>('/localization/process', payload)
}

// 获取最近 20 条本地化历史记录。
export function getLocalizationHistory(params: { project_id?: number | null; episode_id?: number | null; episode_no?: number | null } = {}) {
  return request.get<unknown, ApiResponse<LocalizationHistoryItem[]>>('/localization/list', { params })
}
