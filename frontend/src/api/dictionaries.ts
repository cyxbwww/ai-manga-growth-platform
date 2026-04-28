import request from '../utils/request'
import type { ApiResponse } from '../types/common'
import type { DictionaryOption, DictionaryResponse } from '../types/dictionary'

// 一次性加载全部业务字典，供生成页、项目页和选择器复用。
export function getDictionaries() {
  return request.get<unknown, ApiResponse<DictionaryResponse>>('/dictionaries')
}

// 按类型加载字典，预留给后续需要单独刷新某类字典的场景。
export function getDictionary(dictType: string) {
  return request.get<unknown, ApiResponse<DictionaryOption[]>>(`/dictionaries/${dictType}`)
}
