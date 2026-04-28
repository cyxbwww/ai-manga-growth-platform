// ???????Episode ??????????????
export type ShortDramaEpisodeStage = 'planning' | 'scripting' | 'storyboard' | 'localization' | 'media' | 'completed'

// ??????????????????????????
export type ShortDramaEpisodeStatus = 'active' | 'paused' | 'completed' | 'archived'

// ??????????????????????????????
export type ShortDramaEpisodeSubStatus = 'pending' | 'processing' | 'completed' | 'failed' | string

export type ShortDramaEpisode = {
  id: number
  project_id: number
  episode_no: number
  title: string
  summary?: string | null
  stage: ShortDramaEpisodeStage
  status: ShortDramaEpisodeStatus
  script_status?: ShortDramaEpisodeSubStatus | null
  storyboard_status?: ShortDramaEpisodeSubStatus | null
  localization_status?: ShortDramaEpisodeSubStatus | null
  media_status?: ShortDramaEpisodeSubStatus | null
  // ?????????????? projectId + episodeId ???
  storyboard_count?: number
  localization_count?: number
  media_asset_count?: number
  ad_material_count?: number
  created_at: string
  updated_at: string
}

export type ShortDramaEpisodeCreate = {
  project_id: number
  episode_no: number
  title: string
  summary?: string | null
  stage?: ShortDramaEpisodeStage
  status?: ShortDramaEpisodeStatus
}

export type ShortDramaEpisodeUpdate = Partial<{
  episode_no: number
  title: string
  summary: string | null
  stage: ShortDramaEpisodeStage
  status: ShortDramaEpisodeStatus
  script_status: ShortDramaEpisodeSubStatus
  storyboard_status: ShortDramaEpisodeSubStatus
  localization_status: ShortDramaEpisodeSubStatus
  media_status: ShortDramaEpisodeSubStatus
}>

export type ShortDramaEpisodeListParams = {
  keyword?: string
  stage?: ShortDramaEpisodeStage
  status?: ShortDramaEpisodeStatus
  skip?: number
  limit?: number
}

export type ShortDramaEpisodeListResponse = {
  items: ShortDramaEpisode[]
  total: number
}

export type EpisodeOutlineGeneratePayload = {
  content_plan_id?: number | null
  episode_count: number
  start_episode_no: number
  overwrite: boolean
}

export type EpisodeOutlineGenerateResponse = {
  project_id: number
  content_plan_id?: number | null
  generation_source?: 'deepseek' | 'rule_fallback' | string
  created_count: number
  updated_count: number
  skipped_count: number
  items: ShortDramaEpisode[]
}
