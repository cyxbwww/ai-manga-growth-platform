// 后端统一响应结构：所有业务接口都包在 code/message/data 中。
export type ApiResponse<T> = {
  code: number
  message: string
  data: T
}
