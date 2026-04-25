// 后端签名请求：只传元数据，文件本体不经过 FastAPI。
export type MediaPresignRequest = {
  filename: string
  mimeType: string
  size: number
}

export type MediaPresignResult = {
  assetId: number
  uploadUrl: string
  objectKey: string
  publicUrl: string
  provider: 's3' | 'mock'
}

export type MediaCompleteRequest = {
  assetId: number
  objectKey: string
}

export type MediaAsset = {
  id: number
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
