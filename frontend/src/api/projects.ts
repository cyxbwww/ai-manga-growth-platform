import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type {
  ShortDramaProject,
  ShortDramaProjectCreate,
  ShortDramaProjectListParams,
  ShortDramaProjectListResponse,
  ShortDramaProjectUpdate,
  ProjectOverview,
} from '../types/project'

// 查询短剧项目列表：支持关键词、题材、阶段、状态筛选，后续可继续接分页器。
export function getProjects(params: ShortDramaProjectListParams = {}) {
  return request.get<unknown, ApiResponse<ShortDramaProjectListResponse>>('/projects', { params })
}

// 新建短剧项目：作为后续 AI 生产链路的业务主线。
export function createProject(data: ShortDramaProjectCreate) {
  return request.post<unknown, ApiResponse<ShortDramaProject>>('/projects', data)
}

// 查询项目详情：当前第一步先预留给后续详情页接入。
export function getProjectDetail(id: number) {
  return request.get<unknown, ApiResponse<ShortDramaProject>>(`/projects/${id}`)
}

// 查询项目总览：用于项目详情页一次性展示基础信息、统计、生产链路和最近资产。
export function getProjectOverview(id: number | string) {
  return request.get<unknown, ApiResponse<ProjectOverview>>(`/projects/${id}/overview`)
}

// 更新短剧项目基础信息。
export function updateProject(id: number, data: ShortDramaProjectUpdate) {
  return request.patch<unknown, ApiResponse<ShortDramaProject>>(`/projects/${id}`, data)
}

// 归档项目：后端采用软删除，把 status 改为 archived。
export function archiveProject(id: number) {
  return request.delete<unknown, ApiResponse<ShortDramaProject>>(`/projects/${id}`)
}
