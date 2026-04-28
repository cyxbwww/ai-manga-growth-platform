import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type {
  EpisodeOutlineGeneratePayload,
  EpisodeOutlineGenerateResponse,
  ShortDramaEpisode,
  ShortDramaEpisodeCreate,
  ShortDramaEpisodeListParams,
  ShortDramaEpisodeListResponse,
  ShortDramaEpisodeUpdate,
} from '../types/episode'

// 查询项目下的分集列表，支持筛选和分页。
export function getProjectEpisodes(projectId: number | string, params: ShortDramaEpisodeListParams = {}) {
  return request.get<unknown, ApiResponse<ShortDramaEpisodeListResponse>>(`/projects/${projectId}/episodes`, { params })
}

// 给短剧项目新增一个分集。
export function createProjectEpisode(projectId: number | string, data: ShortDramaEpisodeCreate) {
  return request.post<unknown, ApiResponse<ShortDramaEpisode>>(`/projects/${projectId}/episodes`, data)
}

// 查询单个分集详情，后续分集详情页可复用。
export function getEpisodeDetail(episodeId: number | string) {
  return request.get<unknown, ApiResponse<ShortDramaEpisode>>(`/episodes/${episodeId}`)
}

// 编辑分集基础信息或生产状态。
export function updateEpisode(episodeId: number | string, data: ShortDramaEpisodeUpdate) {
  return request.patch<unknown, ApiResponse<ShortDramaEpisode>>(`/episodes/${episodeId}`, data)
}

// 归档分集，后端执行软删除。
export function archiveEpisode(episodeId: number | string) {
  return request.delete<unknown, ApiResponse<ShortDramaEpisode>>(`/episodes/${episodeId}`)
}

// 根据项目计划集数批量生成分集骨架。
export function batchGenerateEpisodes(projectId: number | string) {
  return request.post<unknown, ApiResponse<ShortDramaEpisodeListResponse>>(`/projects/${projectId}/episodes/batch-generate`)
}

// 从内容策划结果生成分集大纲初稿，生成后仍在分集管理页逐集调整。
export function generateEpisodeOutline(projectId: number | string, data: EpisodeOutlineGeneratePayload) {
  return request.post<unknown, ApiResponse<EpisodeOutlineGenerateResponse>>(`/projects/${projectId}/episodes/generate-outline`, data)
}
