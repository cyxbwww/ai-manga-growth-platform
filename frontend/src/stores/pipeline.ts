import { defineStore } from 'pinia'

type PipelineState = {
  contentPlanId: number | null
  scriptPolishId: number | null
  storyboardId: number | null
  localizationId: number | null
  adMaterialId: number | null
}

const STORAGE_KEY = 'ai_manga_pipeline_state'

function loadState(): PipelineState {
  // 刷新页面后从 localStorage 恢复当前生产链路。
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) throw new Error('empty')
    return JSON.parse(raw) as PipelineState
  } catch {
    return { contentPlanId: null, scriptPolishId: null, storyboardId: null, localizationId: null, adMaterialId: null }
  }
}

export const usePipelineStore = defineStore('pipeline', {
  state: (): PipelineState => loadState(),
  actions: {
    persist() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.$state))
    },
    setContentPlanId(id: number | null) {
      this.contentPlanId = id
      if (!id) this.resetDownstream('content')
      this.persist()
    },
    setScriptPolishId(id: number | null) {
      this.scriptPolishId = id
      if (!id) this.resetDownstream('script')
      this.persist()
    },
    setStoryboardId(id: number | null) {
      this.storyboardId = id
      if (!id) this.resetDownstream('storyboard')
      this.persist()
    },
    setLocalizationId(id: number | null) {
      this.localizationId = id
      if (!id) this.adMaterialId = null
      this.persist()
    },
    setAdMaterialId(id: number | null) {
      this.adMaterialId = id
      this.persist()
    },
    resetDownstream(from: 'content' | 'script' | 'storyboard') {
      if (from === 'content') this.scriptPolishId = null
      if (from === 'content' || from === 'script') this.storyboardId = null
      if (from === 'content' || from === 'script' || from === 'storyboard') this.localizationId = null
      this.adMaterialId = null
    },
    resetPipeline() {
      this.contentPlanId = null
      this.scriptPolishId = null
      this.storyboardId = null
      this.localizationId = null
      this.adMaterialId = null
      this.persist()
    },
  },
})
