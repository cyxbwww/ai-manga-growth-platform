// 后端签名请求：只传元数据，文件本体不经过 FastAPI。
export type MediaPresignRequest = {
  filename: string
  mimeType: string
  size: number
  // project_id 用于把媒体资产归属到短剧项目；presign 阶段创建元数据时写入。
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
}

export type MediaPresignResult = {
  assetId: number
  uploadUrl: string
  objectKey: string
  publicUrl: string
  provider: 's3' | 'mock'
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
}

export type MediaCompleteRequest = {
  assetId: number
  objectKey: string
  // complete 阶段允许补写 project_id，兼容未绑定项目的旧上传流程。
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
}

export type MediaAsset = {
  id: number
  project_id?: number | null
  episode_id?: number | null
  episode_no?: number | null
  filename: string
  originalFilename: string
  fileType: 'video' | 'image' | 'subtitle'
  mimeType: string
  size: number
  objectKey: string
  url: string
  provider: 's3' | 'mock'
  status: 'pending' | 'uploaded' | 'failed'
  createdAt: string
}
