import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type {
  LocalizationHistoryItem,
  LocalizationProcessRequest,
  LocalizationProcessResult,
} from '../types/localization'

// 执行多语种本地化，并把当前链路 ID 一起传给后端保存。
export function processLocalization(payload: LocalizationProcessRequest) {
  return request.post<unknown, ApiResponse<LocalizationProcessResult>>('/localization/process', payload)
}

// 获取最近 20 条本地化历史记录。
export function getLocalizationHistory() {
  return request.get<unknown, ApiResponse<LocalizationHistoryItem[]>>('/localization/list')
}
