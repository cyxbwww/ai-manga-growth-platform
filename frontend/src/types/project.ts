// 短剧项目阶段：用于表示项目当前处在生产链路的哪一步。
export type ShortDramaProjectStage = 'planning' | 'scripting' | 'storyboard' | 'localization' | 'material' | 'launch' | 'completed'

// 短剧项目状态：归档是软删除状态，不会物理删除项目。
export type ShortDramaProjectStatus = 'active' | 'paused' | 'completed' | 'archived'

// 项目优先级：用于后台列表快速判断推进顺序。
export type ShortDramaProjectPriority = 'high' | 'medium' | 'low'

// 后端返回的短剧项目结构，字段与数据库模型保持一致。
export type ShortDramaProject = {
  id: number
  name: string
  genre: string | undefined
  target_market: string | undefined
  language: string
  episode_count: number
  stage: ShortDramaProjectStage
  description?: string | null
  owner?: string | null
  priority: ShortDramaProjectPriority
  status: ShortDramaProjectStatus
  created_at: string
  updated_at: string
}

export type ShortDramaProjectCreate = {
  name: string
  genre: string | undefined
  target_market: string | undefined
  language: string
  episode_count: number
  stage: ShortDramaProjectStage
  description?: string | null
  owner?: string | null
  priority: ShortDramaProjectPriority
  status: ShortDramaProjectStatus
}

export type ShortDramaProjectUpdate = Partial<ShortDramaProjectCreate>

export type ShortDramaProjectListParams = {
  keyword?: string
  genre?: string | undefined
  stage?: ShortDramaProjectStage | undefined
  status?: ShortDramaProjectStatus | undefined
  skip?: number
  limit?: number
}

export type ShortDramaProjectListResponse = {
  items: ShortDramaProject[]
  total: number
}

// 项目详情统计：用于项目工作台展示各生产环节资产数量。
export type ProjectStats = {
  content_plan_count: number
  episode_count: number
  script_count: number
  storyboard_count: number
  localization_count: number
  ad_material_count: number
  media_asset_count: number
}

// 项目生产链路节点：描述每个 AI 短剧生产阶段的状态和资产数量。
export type ProjectPipelineItem = {
  key: string
  title: string
  status: 'completed' | 'processing' | 'pending'
  count: number
  description: string
}

// 最近数据条目：用于展示最近分镜、广告素材和媒体资产。
export type ProjectRecentItem = {
  id: number
  title: string
  type: string
  status: string
  created_at: string
  episode_id?: number | null
  episode_no?: number | null
}

// 项目详情聚合数据：一个接口支撑项目详情页的基础信息、统计、链路和最近数据。
export type ProjectOverview = {
  project: ShortDramaProject
  stats: ProjectStats
  pipeline: ProjectPipelineItem[]
  recent_storyboards: ProjectRecentItem[]
  recent_ad_materials: ProjectRecentItem[]
  recent_media_assets: ProjectRecentItem[]
}
