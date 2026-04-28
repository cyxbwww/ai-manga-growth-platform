<template>
  <div class="dictionary-page">
    <n-card bordered class="intro-card">
      <div class="intro-header">
        <div>
          <h2>字典管理</h2>
          <p>当前字典由后端静态配置提供，用于统一目标市场、语言、题材、阶段、状态等业务选项。后续可升级为数据库字典表或配置中心。</p>
        </div>
        <n-button secondary :loading="loading" @click="loadDictionaryPage">刷新</n-button>
      </div>
    </n-card>

    <n-alert v-if="errorMessage" type="warning" :bordered="false" class="state-alert">
      {{ errorMessage }}
    </n-alert>

    <n-card title="业务字典配置" bordered class="table-card">
      <template #header-extra>
        <n-tag type="info" :bordered="false">只读</n-tag>
      </template>

      <div class="filter-bar">
        <n-input
          v-model:value="keyword"
          clearable
          placeholder="搜索标签或值"
        />
        <n-tag :bordered="false">共 {{ filteredTotal }} 项</n-tag>
      </div>

      <n-spin :show="loading">
        <n-empty v-if="!hasAnyDictionary" description="暂无字典配置" class="empty-block" />
        <n-tabs v-else v-model:value="activeTab" type="line" animated>
          <n-tab-pane
            v-for="group in dictionaryGroups"
            :key="group.key"
            :name="group.key"
            :tab="`${group.label}（${filteredDictionaries[group.key].length}）`"
          >
            <n-data-table
              :columns="columns"
              :data="filteredDictionaries[group.key]"
              :bordered="false"
              :single-line="false"
              :pagination="false"
              class="dictionary-table"
            >
              <template #empty>
                <n-empty description="当前分组暂无匹配字典项" />
              </template>
            </n-data-table>
          </n-tab-pane>
        </n-tabs>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NTag } from 'naive-ui'
import { getDictionaries } from '../api/dictionaries'
import { fallbackDictionaries, useDictionaries } from '../composables/useDictionaries'
import type { DictionaryOption, DictionaryResponse } from '../types/dictionary'

type DictionaryKey = keyof DictionaryResponse

type DictionaryGroup = {
  key: DictionaryKey
  label: string
}

type DictionaryRow = DictionaryOption & {
  dict_type: DictionaryKey
}

const dictionaryGroups: DictionaryGroup[] = [
  { key: 'markets', label: '目标市场' },
  { key: 'languages', label: '语言' },
  { key: 'genres', label: '题材' },
  { key: 'project_stages', label: '项目阶段' },
  { key: 'project_statuses', label: '项目状态' },
  { key: 'priorities', label: '优先级' },
]

const { dictionaries } = useDictionaries()
const loading = ref(false)
const keyword = ref('')
const activeTab = ref<DictionaryKey>('markets')
const errorMessage = ref('')

const dictionaryRows = computed<Record<DictionaryKey, DictionaryRow[]>>(() => {
  return dictionaryGroups.reduce((result, group) => {
    result[group.key] = (dictionaries.value[group.key] || []).map((item) => ({
      ...item,
      dict_type: group.key,
    }))
    return result
  }, {} as Record<DictionaryKey, DictionaryRow[]>)
})

const filteredDictionaries = computed<Record<DictionaryKey, DictionaryRow[]>>(() => {
  const searchText = keyword.value.trim().toLowerCase()
  return dictionaryGroups.reduce((result, group) => {
    const rows = dictionaryRows.value[group.key]
    result[group.key] = searchText
      ? rows.filter((item) => item.label.toLowerCase().includes(searchText) || item.value.toLowerCase().includes(searchText))
      : rows
    return result
  }, {} as Record<DictionaryKey, DictionaryRow[]>)
})

const hasAnyDictionary = computed(() => dictionaryGroups.some((group) => dictionaryRows.value[group.key].length > 0))
const filteredTotal = computed(() => dictionaryGroups.reduce((total, group) => total + filteredDictionaries.value[group.key].length, 0))

const columns: DataTableColumns<DictionaryRow> = [
  {
    title: '序号',
    key: 'index',
    width: 80,
    render: (_row, index) => index + 1,
  },
  {
    title: '标签 label',
    key: 'label',
    minWidth: 180,
  },
  {
    title: '值 value',
    key: 'value',
    minWidth: 180,
  },
  {
    title: '字典类型 dict_type',
    key: 'dict_type',
    minWidth: 180,
    render(row) {
      return h(NTag, { bordered: false, type: 'success' }, { default: () => row.dict_type })
    },
  },
]

async function loadDictionaryPage() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await getDictionaries()
    if (response.code !== 0) {
      throw new Error(response.message || '字典接口返回异常')
    }
    dictionaries.value = response.data
  } catch {
    // 接口失败时显式切换到前端 fallback，保证系统配置页离线演示也可稳定查看。
    dictionaries.value = fallbackDictionaries
    errorMessage.value = '字典接口异常，当前展示前端 fallback 字典。'
  } finally {
    loading.value = false
  }
}

onMounted(loadDictionaryPage)
</script>

<style scoped>
.dictionary-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.intro-card,
.table-card {
  border-radius: 8px;
}

.intro-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.intro-header h2 {
  margin: 0;
  color: #111827;
  font-size: 22px;
}

.intro-header p {
  max-width: 820px;
  margin: 8px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.state-alert {
  border-radius: 8px;
}

.filter-bar {
  display: grid;
  grid-template-columns: minmax(260px, 420px) max-content;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.dictionary-table {
  margin-top: 4px;
}

.empty-block {
  padding: 56px 0;
}

@media (max-width: 720px) {
  .intro-header {
    flex-direction: column;
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
