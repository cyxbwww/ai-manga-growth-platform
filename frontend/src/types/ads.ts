// 广告素材生成请求：可携带上游链路 ID，也可作为独立页面使用。
export type AdsGenerateRequest = {
  projectName: string
  market: string
  platform: string
  contentType: string
  // project_id 用于把广告素材归属到短剧项目；不传时仍可独立生成。
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  contentPlanId?: number | null
  scriptPolishId?: number | null
  storyboardId?: number | null
  localizationId?: number | null
}

// 单条广告素材：支持前端标记推荐和复制文案。
export type AdCopyItem = {
  id: number
  title: string
  hook: string
  copy: string
  recommended: boolean
}

// 广告素材双语字段：目标语言用于海外投放，中文用于团队审核。
export type AdsBilingualFields = {
  titles: string[]
  hooks: string[]
  copies: string[]
  cta: string[]
  coverPrompt: string
  abTestSuggestions: string[]
}

// 广告素材生成结果：bilingual 可选，兼容旧历史数据。
export type AdsGenerateResult = {
  recordId?: number
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  projectName: string
  market: string
  platform: string
  contentType: string
  titles: string[]
  hooks: string[]
  copies: AdCopyItem[]
  cta: string[]
  coverPrompt: string
  abTestSuggestions: string[]
  bilingual?: {
    zh: AdsBilingualFields
    target: AdsBilingualFields & {
      language: string
    }
  }
}

// 广告素材历史记录：保留输入条件、链路 ID 和素材包结果。
export type AdMaterialHistoryItem = AdsGenerateRequest & {
  id: number
  recordId?: number
  result: AdsGenerateResult
  createdAt: string
}
