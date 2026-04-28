// 分镜生成请求：可携带内容策划和剧本打磨的上游链路 ID。
export type StoryboardGenerateRequest = {
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  title: string
  script: string
  style: string
  sceneCount: number
  contentPlanId?: number | null
  scriptPolishId?: number | null
}

// 单个分镜的文本字段：兼容旧顶层字段和新版 bilingual 对象字段。
export type StoryboardSceneText = {
  title?: string
  scene?: string
  characterAction?: string
  dialogue?: string
  emotion?: string
  visualPrompt?: string
  motionPrompt?: string
  consistencyPrompt?: string
}

// 单个分镜数据：bilingual 可选，并兼容 string / object 两种返回形式。
export type StoryboardScene = StoryboardSceneText & {
  sceneNo?: number
  sceneNumber?: number
  duration?: string
  status?: string
  bilingual?: {
    zh?: string | StoryboardSceneText
    target?: string | (StoryboardSceneText & { language?: string })
  }
}

// 归一化后用于页面展示的分镜字段，所有字段都有兜底文本。
export type StoryboardSceneDisplay = Required<StoryboardSceneText> & {
  sceneNo: number
  duration: string
  status: string
}

// 分镜生成结果：右侧以卡片形式展示可生产化内容。
export type StoryboardGenerateResult = {
  recordId?: number
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  storyboardTitle: string
  style: string
  scenes: StoryboardScene[]
}

// 分镜历史记录：保存核心输入字段、链路 ID 和完整分镜结果。
export type StoryboardHistoryItem = StoryboardGenerateRequest & {
  id: number
  recordId?: number
  episode_id?: number | null
  episode_no?: number | null
  result: StoryboardGenerateResult
  createdAt: string
}
