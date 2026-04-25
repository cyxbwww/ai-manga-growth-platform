// 内容策划请求参数：对应后端 POST /api/content/plan。
export type ContentPlanRequest = {
  projectName: string
  genre: string
  market: string
  language: string
  duration: string
  sellingPoint: string
}

// 内容策划双语字段：用于中文审核版和目标语言投放版切换。
export type ContentPlanBilingualFields = {
  title: string
  positioning: string
  targetAudience: string
  coreConflict: string
  emotionHook: string
  openingHook: string
  highlights: string[]
  platforms: string[]
  suggestions: string[]
}

// 内容策划返回结果：bilingual 为可选字段，用于兼容旧历史数据。
export type ContentPlanResult = ContentPlanBilingualFields & {
  recordId?: number
  bilingual?: {
    zh: ContentPlanBilingualFields
    target: ContentPlanBilingualFields & {
      language: string
    }
  }
}

// 内容策划历史记录：后端会把 result_json 解析为 result 对象返回。
export type ContentPlanHistoryItem = ContentPlanRequest & {
  id: number
  recordId?: number
  result: ContentPlanResult
  createdAt: string
}
