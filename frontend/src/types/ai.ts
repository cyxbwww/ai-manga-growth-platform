// AI 状态：只展示是否配置 Key，不展示真实密钥。
export type AiStatus = {
  provider: string
  model: string
  enabled: boolean
  hasApiKey: boolean
  baseUrl: string
}
