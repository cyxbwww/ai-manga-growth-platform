// 分镜生成请求：可携带内容策划和剧本打磨的上游链路 ID。
export type StoryboardGenerateRequest = {
  title: string
  script: string
  style: string
  sceneCount: number
  contentPlanId?: number | null
  scriptPolishId?: number | null
}

// 单个分镜的可切换双语字段。
export type StoryboardSceneBilingualFields = {
  title: string
  scene: string
  characterAction: string
  dialogue: string
  emotion: string
  visualPrompt: string
  motionPrompt: string
  consistencyPrompt: string
}

// 单个分镜数据：bilingual 可选，兼容旧历史记录。
export type StoryboardScene = StoryboardSceneBilingualFields & {
  sceneNo: number
  duration: string
  status: string
  bilingual?: {
    zh: StoryboardSceneBilingualFields
    target: StoryboardSceneBilingualFields & {
      language: string
    }
  }
}

// 分镜生成结果：右侧以卡片形式展示可生产化内容。
export type StoryboardGenerateResult = {
  recordId?: number
  storyboardTitle: string
  style: string
  scenes: StoryboardScene[]
}

// 分镜历史记录：保存核心输入字段、链路 ID 和完整分镜结果。
export type StoryboardHistoryItem = StoryboardGenerateRequest & {
  id: number
  recordId?: number
  result: StoryboardGenerateResult
  createdAt: string
}
