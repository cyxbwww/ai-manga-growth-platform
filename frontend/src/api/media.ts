import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { MediaAsset, MediaCompleteRequest, MediaPresignRequest, MediaPresignResult } from '../types/media'

// 获取单文件 PUT 上传签名，后端只保存 pending 元数据。
export function presignMedia(payload: MediaPresignRequest) {
  return request.post<unknown, ApiResponse<MediaPresignResult>>('/media/presign', payload)
}

// 前端直传完成后通知后端更新素材状态。
export function completeMediaUpload(payload: MediaCompleteRequest) {
  return request.post<unknown, ApiResponse<MediaAsset>>('/media/complete', payload)
}

// 获取最近 50 条素材记录。
export function getMediaAssets(params: { project_id?: number | null; episode_id?: number | null; episode_no?: number | null } = {}) {
  return request.get<unknown, ApiResponse<MediaAsset[]>>('/media/assets', { params })
}

export function getMediaAsset(assetId: number) {
  return request.get<unknown, ApiResponse<MediaAsset>>(`/media/assets/${assetId}`)
}
