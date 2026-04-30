// 本地化处理请求：projectId + episodeId + sourceText 是本地化链路的核心上下文。
export type LocalizationProcessRequest = {
  projectId?: number | null
  episodeId?: number | null
  episodeNo?: number | null
  sourceText: string
  targetMarket: string
  targetLanguage: string
  strategy: string
  // 以下 snake_case 字段仅用于兼容旧历史数据和旧接口返回。
  market?: string
  language?: string
  source_text?: string | null
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

// 改写对比：用于说明本地化不是逐字翻译，而是在保留剧情含义的基础上做文化适配。
export type LocalizationComparisonItem = {
  originalText: string
  directTranslation: string
  localizedText: string
}

// 本地化处理结果：recordId 是当前持久化记录 ID。
export type LocalizationProcessResult = {
  recordId?: number
  projectId?: number | null
  episodeId?: number | null
  episodeNo?: number | null
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  sourceText?: string
  targetMarket?: string
  targetLanguage?: string
  market: string
  language: string
  strategy: string
  subtitles: LocalizedSubtitle[]
  comparison: LocalizationComparisonItem[]
  workflowSteps: LocalizationWorkflowItem[]
  workflow?: LocalizationWorkflowItem[]
  status: string
}

// 本地化历史记录：保留输入条件、链路 ID 和处理结果；旧记录可能只有 market/language。
export type LocalizationHistoryItem = Omit<LocalizationProcessRequest, 'market' | 'language' | 'sourceText' | 'targetMarket' | 'targetLanguage'> & {
  id: number
  recordId?: number
  market: string
  language: string
  sourceText?: string
  targetMarket?: string
  targetLanguage?: string
  result: LocalizationProcessResult
  createdAt: string
}
