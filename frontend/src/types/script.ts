// 剧本打磨请求参数：language 保存字典 value，例如 en-US；directions 支持多个优化方向。
export type ScriptPolishRequest = {
  project_id?: number | null
  language?: string | null
  target_language?: string | null
  title: string
  script: string
  directions: string[]
  contentPlanId?: number | null
}

// 单条诊断项：描述问题类型、发现的问题和对应建议。
export type ScriptDiagnostic = {
  type: string
  problem: string
  suggestion: string
}

// 海外本地化改写项：展示直译和本地化表达差异。
export type LocalizedRewrite = {
  original: string
  directTranslation: string
  localizedVersion: string
}

// 剧本打磨双语字段：只影响优化后剧本和优化建议展示。
export type ScriptPolishBilingualFields = {
  polishedScript: string
  optimizationTips: string[]
}

// 剧本打磨返回结果：bilingual 可选，兼容旧历史数据。
export type ScriptPolishResult = {
  recordId?: number
  language?: string
  target_language?: string
  score: number
  diagnostics: ScriptDiagnostic[]
  polishedScript: string
  localizedRewrite: LocalizedRewrite[]
  optimizationTips: string[]
  bilingual?: {
    zh: ScriptPolishBilingualFields
    target: ScriptPolishBilingualFields & {
      language: string
    }
  }
}

// 剧本打磨历史记录：用于刷新页面后查看已生成结果。
export type ScriptPolishHistoryItem = ScriptPolishRequest & {
  id: number
  recordId?: number
  language?: string | null
  target_language?: string | null
  result: ScriptPolishResult
  createdAt: string
}
