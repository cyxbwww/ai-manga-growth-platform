import { ref } from 'vue'
import { getDictionaries } from '../api/dictionaries'
import type { DictionaryResponse } from '../types/dictionary'

const fallbackDictionaries: DictionaryResponse = {
  markets: ['中国大陆', '北美', '东南亚', '日本', '韩国', '中东', '欧洲', '拉美'].map((item) => ({ label: item, value: item })),
  languages: [
    { label: '中文（zh-CN）', value: 'zh-CN' },
    { label: '英文（en-US）', value: 'en-US' },
    { label: '日文（ja-JP）', value: 'ja-JP' },
    { label: '韩文（ko-KR）', value: 'ko-KR' },
    { label: '泰文（th-TH）', value: 'th-TH' },
    { label: '印尼文（id-ID）', value: 'id-ID' },
    { label: '阿拉伯文（ar-SA）', value: 'ar-SA' },
    { label: '西班牙文（es-ES）', value: 'es-ES' },
  ],
  genres: ['都市逆袭', '情感爽剧', '女性成长', '甜宠', '悬疑', '复仇'].map((item) => ({ label: item, value: item })),
  project_stages: [
    { label: '策划中', value: 'planning' },
    { label: '剧本中', value: 'scripting' },
    { label: '分镜中', value: 'storyboard' },
    { label: '本地化中', value: 'localization' },
    { label: '素材制作中', value: 'material' },
    { label: '投放中', value: 'launch' },
    { label: '已完成', value: 'completed' },
  ],
  project_statuses: [
    { label: '进行中', value: 'active' },
    { label: '已暂停', value: 'paused' },
    { label: '已完成', value: 'completed' },
    { label: '已归档', value: 'archived' },
  ],
  priorities: [
    { label: '高', value: 'high' },
    { label: '中', value: 'medium' },
    { label: '低', value: 'low' },
  ],
}

const dictionaries = ref<DictionaryResponse>(fallbackDictionaries)
const loading = ref(false)
let loaded = false

export function useDictionaries() {
  async function loadDictionaries() {
    if (loaded) return
    loading.value = true
    try {
      const response = await getDictionaries()
      if (response.code === 0) {
        dictionaries.value = response.data
        loaded = true
      }
    } catch {
      // 字典接口异常时使用前端 fallback，保证本地和面试演示页面仍可使用。
      dictionaries.value = fallbackDictionaries
      loaded = true
    } finally {
      loading.value = false
    }
  }

  function getLabel(dictKey: keyof DictionaryResponse, value?: string | null) {
    if (!value) return '-'
    return dictionaries.value[dictKey]?.find((item) => item.value === value)?.label || value
  }

  return {
    dictionaries,
    loading,
    loadDictionaries,
    getLabel,
  }
}
