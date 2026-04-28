// 本地化处理请求：支持携带上游链路 ID，字段可为空以兼容独立使用。
export type LocalizationProcessRequest = {
  market: string
  language: string
  strategy: string
  // project_id 用于把本地化结果归属到短剧项目；可为空以兼容独立使用。
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  contentPlanId?: number | null
  scriptPolishId?: number | null
  storyboardId?: number | null
}

// 单条字幕：覆盖翻译、配音、口型匹配和字幕处理状态。
export type LocalizedSubtitle = {
  index: number
  startTime: string
  endTime: string
  originalText: string
  directTranslation: string
  localizedText: string
  voiceStatus: string
  lipSyncStatus: string
  subtitleStatus: string
}

// 本地化流程节点：用于右侧流程卡片展示生产进度。
export type LocalizationWorkflowItem = {
  step: string
  status: string
  description: string
}

// 本地化处理结果：recordId 是当前持久化记录 ID。
export type LocalizationProcessResult = {
  recordId?: number
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  market: string
  language: string
  strategy: string
  subtitles: LocalizedSubtitle[]
  workflow: LocalizationWorkflowItem[]
}

// 本地化历史记录：保留输入条件、链路 ID 和处理结果。
export type LocalizationHistoryItem = LocalizationProcessRequest & {
  id: number
  recordId?: number
  result: LocalizationProcessResult
  createdAt: string
}
