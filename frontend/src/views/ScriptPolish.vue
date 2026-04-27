<template>
  <div class="module-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="剧本输入" :bordered="false">
            <n-alert v-if="pipeline.contentPlanId" type="success" :bordered="false" class="pipeline-tip">
              已绑定内容策划 ID：{{ pipeline.contentPlanId }}，生成时会写入完整生产链路。
            </n-alert>
            <n-alert v-else type="info" :bordered="false" class="pipeline-tip">
              当前页面可独立使用，也可从内容策划进入以自动带入标题和剧本草稿。
            </n-alert>

            <n-form :model="form" label-placement="top">
              <n-form-item label="剧本标题">
                <n-input v-model:value="form.title" placeholder="例如：她在婚礼当天醒悟" />
              </n-form-item>
              <n-form-item label="原始剧本文本">
                <n-input v-model:value="form.script" type="textarea" :autosize="{ minRows: 10, maxRows: 16 }" />
              </n-form-item>
              <n-form-item label="打磨方向">
                <n-checkbox-group v-model:value="form.directions">
                  <n-space vertical>
                    <n-checkbox value="强化前三秒钩子">强化前三秒钩子</n-checkbox>
                    <n-checkbox value="增强冲突">增强冲突</n-checkbox>
                    <n-checkbox value="加强反转">加强反转</n-checkbox>
                    <n-checkbox value="提升情绪张力">提升情绪张力</n-checkbox>
                    <n-checkbox value="适配海外表达">适配海外表达</n-checkbox>
                  </n-space>
                </n-checkbox-group>
              </n-form-item>
              <n-button type="primary" block size="large" :loading="loading" @click="handlePolish">开始打磨</n-button>
            </n-form>
          </n-card>

          <n-card title="历史记录" :bordered="false">
            <n-list v-if="history.length" hoverable clickable>
              <n-list-item v-for="item in history" :key="item.id" @click="selectHistory(item)">
                <n-thing :title="item.title" :description="formatTime(item.createdAt)">
                  <template #header-extra>
                    <n-tag type="warning" bordered>{{ item.result.score }}分</n-tag>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
            <n-empty v-else description="暂无历史记录，打磨后会自动保存。" />
          </n-card>
        </n-space>
      </n-grid-item>

      <n-grid-item :span="16" :s-span="24">
        <n-spin :show="loading">
          <n-card title="AI编剧打磨工作台" :bordered="false" class="result-card">
            <template #header-extra>
              <n-space align="center">
                <n-radio-group v-if="result?.bilingual" v-model:value="displayLanguage" size="small">
                  <n-radio-button value="zh">中文</n-radio-button>
                  <n-radio-button value="target">{{ result.bilingual.target.language || '目标语言' }}</n-radio-button>
                </n-radio-group>
                <n-tag type="info" bordered>辅助内容精品化</n-tag>
              </n-space>
            </template>

            <template v-if="result">
              <section class="score-panel">
                <div class="score-main">
                  <n-progress type="circle" :percentage="result.score" :height="94" status="success" />
                  <div>
                    <div class="score-title">剧本综合评分</div>
                    <div class="score-copy">AI 从节奏、冲突、反转和情绪张力四个维度辅助判断剧本可投放性。</div>
                  </div>
                </div>
                <div class="score-dimensions">
                  <div v-for="item in dimensionScores" :key="item.label" class="dimension-item">
                    <div class="dimension-head">
                      <span>{{ item.label }}</span>
                      <strong>{{ item.value }}</strong>
                    </div>
                    <n-progress type="line" :percentage="item.value" :height="8" :show-indicator="false" status="success" />
                  </div>
                </div>
              </section>

              <n-grid :cols="2" :x-gap="16" :y-gap="16" responsive="screen">
                <n-grid-item>
                  <n-card size="small" title="问题诊断" class="inner-card">
                    <div class="diagnostic-list">
                      <div v-for="item in diagnosticCards" :key="item.type" class="diagnostic-card">
                        <n-tag type="warning" size="small" bordered>{{ item.type }}</n-tag>
                        <div class="diagnostic-row">
                          <span>问题</span>
                          <p>{{ item.problem }}</p>
                        </div>
                        <div class="diagnostic-row">
                          <span>建议</span>
                          <p>{{ item.suggestion }}</p>
                        </div>
                        <div class="diagnostic-row example">
                          <span>示例</span>
                          <p>{{ item.example }}</p>
                        </div>
                      </div>
                    </div>
                  </n-card>
                </n-grid-item>

                <n-grid-item>
                  <n-card size="small" title="优化建议" class="inner-card">
                    <div class="tip-groups">
                      <div v-for="group in tipGroups" :key="group.label" class="tip-group">
                        <n-tag :type="group.type" size="small" bordered>{{ group.label }}</n-tag>
                        <ul>
                          <li v-for="tip in group.items" :key="tip">{{ tip }}</li>
                        </ul>
                      </div>
                    </div>
                  </n-card>
                </n-grid-item>
              </n-grid>

              <n-card size="small" title="优化后剧本片段" class="inner-card">
                <template #header-extra>
                  <n-space>
                    <n-button size="small" secondary @click="copyPolishedScript">复制优化剧本</n-button>
                    <n-button size="small" tertiary @click="replaceOriginalScript">一键替换原剧本</n-button>
                  </n-space>
                </template>
                <pre class="script-output">{{ scriptView.polishedScript }}</pre>
              </n-card>

              <n-card size="small" title="海外本地化改写示例" class="inner-card">
                <div class="localization-note">
                  <strong>直译：</strong>语言翻译，保留原句含义。
                  <strong>本地化表达：</strong>符合目标市场表达习惯，更适合短剧投放。
                </div>
                <n-table :bordered="false" :single-line="false" class="localization-table">
                  <thead>
                    <tr><th>原句</th><th>直译</th><th>本地化表达</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in result.localizedRewrite" :key="item.original">
                      <td>{{ item.original }}</td>
                      <td>{{ item.directTranslation }}</td>
                      <td><div class="localized-highlight">{{ item.localizedVersion }}</div></td>
                    </tr>
                  </tbody>
                </n-table>
              </n-card>

              <div class="next-step-row">
                <n-button type="primary" secondary @click="router.push('/storyboard')">进入分镜制作</n-button>
              </div>
            </template>
            <n-empty v-else description="输入剧本并选择打磨方向，或点击历史记录查看已保存结果。" />
          </n-card>
        </n-spin>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { getPipelineDetail } from '../api/pipeline'
import { getScriptPolishHistory, polishScript } from '../api/script'
import { usePipelineStore } from '../stores/pipeline'
import type { ScriptPolishBilingualFields, ScriptPolishHistoryItem, ScriptPolishRequest, ScriptPolishResult } from '../types/script'

const form = reactive<ScriptPolishRequest>({
  title: '她在婚礼当天醒悟',
  script: '女主站在婚礼现场，发现未婚夫和继妹早已联手骗走她的公司。她没有哭，只是拿出一份合同，说真正的控股人是她。全场安静，未婚夫慌了。',
  directions: ['强化前三秒钩子', '增强冲突', '加强反转', '适配海外表达'],
})

const loading = ref(false)
const result = ref<ScriptPolishResult | null>(null)
const history = ref<ScriptPolishHistoryItem[]>([])
const displayLanguage = ref<'zh' | 'target'>('zh')
const message = useMessage()
const router = useRouter()
const pipeline = usePipelineStore()

const scriptView = computed<ScriptPolishBilingualFields>(() => {
  // 旧历史数据没有 bilingual 时，继续使用顶层中文字段展示。
  if (!result.value?.bilingual) {
    return {
      polishedScript: result.value?.polishedScript || '',
      optimizationTips: result.value?.optimizationTips || [],
    }
  }
  return displayLanguage.value === 'target' ? result.value.bilingual.target : result.value.bilingual.zh
})

const dimensionScores = computed(() => {
  const base = result.value?.score || 0
  return [
    { label: '节奏', value: clampScore(base + 4) },
    { label: '冲突', value: clampScore(base + 2) },
    { label: '反转', value: clampScore(base - 3) },
    { label: '情绪张力', value: clampScore(base + 1) },
  ]
})

const diagnosticExamples = [
  '示例：开场直接给出“合同被公开”或“婚礼现场背叛”，让观众在前三秒理解冲突。',
  '示例：用对手的公开羞辱动作替代解释性旁白，让主角反击更有爽感。',
  '示例：把“我会证明自己”改成“今晚，我拿回他们偷走的一切”。',
]

const diagnosticCards = computed(() =>
  (result.value?.diagnostics || []).map((item, index) => ({
    ...item,
    example: diagnosticExamples[index % diagnosticExamples.length],
  })),
)

const tipGroups = computed(() => {
  const tips = scriptView.value.optimizationTips
  return [
    { label: '剧情优化', type: 'warning' as const, items: tips.filter((_, index) => index % 3 === 0) },
    { label: '表达优化', type: 'info' as const, items: tips.filter((_, index) => index % 3 === 1) },
    { label: '投放优化', type: 'success' as const, items: tips.filter((_, index) => index % 3 === 2) },
  ].map((group) => ({
    ...group,
    items: group.items.length ? group.items : ['当前维度暂无独立建议，可结合其它建议继续优化。'],
  }))
})

function clampScore(value: number) {
  return Math.max(0, Math.min(100, value))
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function selectHistory(item: ScriptPolishHistoryItem) {
  result.value = item.result
  if (item.contentPlanId) pipeline.setContentPlanId(item.contentPlanId)
  pipeline.setScriptPolishId(item.recordId || item.id)
  displayLanguage.value = 'zh'
  message.success('已加载历史打磨结果')
}

async function copyPolishedScript() {
  try {
    await navigator.clipboard.writeText(scriptView.value.polishedScript)
    message.success('优化剧本已复制')
  } catch {
    message.error('复制失败，请手动选择文本复制')
  }
}

function replaceOriginalScript() {
  form.script = scriptView.value.polishedScript
  message.success('已用优化剧本替换原剧本')
}

async function loadHistory() {
  const response = await getScriptPolishHistory()
  if (response.code === 0) {
    history.value = response.data
  }
}

async function hydrateFromPipeline() {
  if (!pipeline.contentPlanId) return
  try {
    const response = await getPipelineDetail(pipeline.contentPlanId)
    const contentPlan = response.data.contentPlan
    const plan = contentPlan?.result
    if (plan) {
      form.title = plan.title || form.title
      form.script = `项目标题：${plan.title || form.title}\n故事定位：${plan.positioning || ''}\n核心冲突：${plan.coreConflict || ''}\n3秒开头：${plan.openingHook || ''}\n\n请基于以上策划生成可用于短视频短剧的剧本草稿。`
    }
  } catch {
    // 自动带入失败不影响页面独立使用。
  }
}

async function handlePolish() {
  if (!form.title.trim() || !form.script.trim()) {
    message.warning('请填写剧本标题和原始剧本文本')
    return
  }

  loading.value = true
  try {
    const response = await polishScript({ ...form, contentPlanId: pipeline.contentPlanId })
    if (response.code === 0) {
      result.value = response.data
      if (response.data.recordId) pipeline.setScriptPolishId(response.data.recordId)
      displayLanguage.value = 'zh'
      await loadHistory()
      message.success('剧本打磨完成并保存')
    }
  } catch {
    message.error('剧本打磨失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadHistory(), hydrateFromPipeline()])
})
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.pipeline-tip {
  margin-bottom: 14px;
}

.result-card {
  min-height: 680px;
}

.result-card :deep(.n-grid-item),
.result-card :deep(.n-list-item),
.result-card :deep(td) {
  min-width: 0;
  white-space: normal !important;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.score-panel {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  margin-bottom: 18px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fbfcff;
}

.score-main {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.score-title {
  color: #111827;
  font-size: 20px;
  font-weight: 800;
}

.score-copy {
  margin-top: 8px;
  color: #4b5563;
  line-height: 1.7;
}

.score-dimensions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-content: center;
}

.dimension-item {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #eef2f7;
  border-radius: 8px;
  background: #ffffff;
}

.dimension-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #374151;
}

.inner-card {
  min-width: 0;
  margin-bottom: 16px;
  background: #fbfcff;
}

.diagnostic-list,
.tip-groups {
  display: grid;
  gap: 12px;
}

.diagnostic-card,
.tip-group {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
}

.diagnostic-row {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 10px;
  margin-top: 8px;
}

.diagnostic-row span {
  color: #6b7280;
  font-size: 12px;
}

.diagnostic-row p {
  margin: 0;
  color: #374151;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.diagnostic-row.example p {
  padding: 8px 10px;
  border-radius: 6px;
  background: #fff7ed;
  color: #9a3412;
}

.tip-group ul {
  margin: 10px 0 0;
  padding-left: 18px;
}

.tip-group li {
  margin-bottom: 8px;
  color: #374151;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.script-output {
  max-height: 280px;
  margin: 0;
  overflow-y: auto;
  color: #374151;
  font-family: "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.localization-note {
  margin-bottom: 12px;
  padding: 10px 12px;
  color: #374151;
  border-radius: 8px;
  background: #f7f8fa;
  line-height: 1.7;
}

.localization-note strong {
  color: #111827;
}

.localized-highlight {
  padding: 8px 10px;
  border-radius: 6px;
  background: #ecfdf5;
  color: #047857;
  font-weight: 700;
  line-height: 1.7;
}

.next-step-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .score-panel {
    grid-template-columns: 1fr;
  }

  .score-dimensions {
    grid-template-columns: 1fr;
  }
}
</style>
