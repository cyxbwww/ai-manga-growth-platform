import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { AdMaterialHistoryItem, AdsGenerateRequest, AdsGenerateResult } from '../types/ads'

// 生成海外投放素材，并把当前链路 ID 一起传给后端保存。
export function generateAds(payload: AdsGenerateRequest) {
  return request.post<unknown, ApiResponse<AdsGenerateResult>>('/ads/generate', payload)
}

// 获取最近 20 条广告素材历史记录。
export function getAdMaterialHistory() {
  return request.get<unknown, ApiResponse<AdMaterialHistoryItem[]>>('/ads/list')
}
