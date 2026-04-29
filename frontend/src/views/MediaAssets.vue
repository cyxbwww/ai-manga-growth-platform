<template>
  <div class="module-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="素材上传" :bordered="false">
            <n-alert type="info" :bordered="false" class="upload-note">
              前端选择文件后，先向后端获取 S3 presigned URL，再由浏览器直传 S3；FastAPI 只保存素材元数据。
            </n-alert>

            <n-form-item label="所属短剧项目">
              <ProjectPicker
                v-model="selectedProjectId"
                placeholder="建议选择短剧项目，方便沉淀到完整生产链路"
                @change="handleProjectChange"
              />
            </n-form-item>
            <n-form-item label="所属分集">
              <EpisodePicker
                v-model="episodeId"
                :project-id="selectedProjectId"
                :episode-no="episodeNo"
                placeholder="请选择要上传媒体资产的具体分集"
                @change="handleEpisodeChange"
              />
            </n-form-item>

            <div v-if="selectedProjectId" class="quick-actions">
              <n-button v-if="selectedProjectId" secondary block class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}`)">
                返回项目详情
              </n-button>
              <n-button v-if="selectedProjectId" secondary block class="project-back-btn" @click="router.push(`/projects/${selectedProjectId}/episodes`)">
                返回分集列表
              </n-button>
            </div>

            <n-alert v-if="selectedProjectId" type="info" :bordered="false" class="context-note">
              {{ mediaContextText }}
            </n-alert>
            <n-card size="small" title="本地化产物管理" class="localized-assets-card">
              <div class="localized-assets-copy">
                当前页面用于管理该分集的海外版本媒体资产，可上传原始视频、目标语言字幕、配音文件、口型匹配后视频和海外预览成片。
              </div>
              <div class="localized-assets-copy">
                多语种本地化生成字幕/配音方向后，可在此上传或关联对应媒体文件，形成当前分集的海外版本资产。
              </div>
              <n-alert :type="episodeId ? 'success' : 'warning'" :bordered="false" class="localized-bind-alert">
                {{ localizedAssetBindText }}
              </n-alert>
              <div class="localized-asset-types">
                <div v-for="item in localizedAssetTypes" :key="item.title" class="localized-asset-type">
                  <div class="localized-asset-title">{{ item.title }}</div>
                  <div class="localized-asset-desc">{{ item.description }}</div>
                </div>
              </div>
            </n-card>

            <div class="upload-box">
              <input ref="fileInputRef" class="file-input" type="file" :accept="acceptTypes" @change="handleFileChange" />
              <n-button type="primary" secondary @click="fileInputRef?.click()">选择视频 / 图片 / 字幕</n-button>
              <div class="upload-hint">支持 mp4、mov、webm、jpg、png、srt</div>
            </div>

            <div v-if="selectedFile" class="file-card">
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="file-meta">{{ normalizeMimeType(selectedFile) }} / {{ formatSize(selectedFile.size) }}</div>
              <n-progress type="line" :percentage="uploadProgress" :status="progressStatus" />
              <div class="upload-status">{{ uploadStatusText }}</div>
              <n-button type="primary" block :loading="uploading" :disabled="!selectedFile" @click="handleUpload">开始上传</n-button>
            </div>
          </n-card>

          <n-card title="上传说明" :bordered="false">
            <n-list>
              <n-list-item>视频最大 500MB，图片最大 20MB，字幕最大 5MB。</n-list-item>
              <n-list-item>S3 真实模式下，PUT 请求只携带 Content-Type，不携带 Authorization。</n-list-item>
              <n-list-item>mock 模式下会模拟进度并保存素材记录，便于本地面试演示。</n-list-item>
            </n-list>
          </n-card>
        </n-space>
      </n-grid-item>

      <n-grid-item :span="16" :s-span="24">
        <n-card title="素材库与预览" :bordered="false" class="asset-card">
          <template #header-extra>
            <n-button size="small" secondary @click="loadAssets()">刷新</n-button>
          </template>

          <n-data-table :columns="columns" :data="assets" :bordered="false" :single-line="false" :loading="loading">
            <template #empty>
              <n-empty v-if="!loading && !assets.length" description="无数据" />
            </template>
          </n-data-table>

          <n-card v-if="previewAsset" size="small" class="preview-card" :title="previewAsset.originalFilename">
            <n-alert v-if="previewAsset.provider === 'mock'" type="warning" :bordered="false" class="preview-alert">
              当前为 mock 素材，未连接真实 S3。这里展示的是元数据预览占位。
            </n-alert>

            <video v-if="previewAsset.fileType === 'video' && previewAsset.provider === 's3'" controls class="media-preview" :src="previewAsset.url" />
            <img v-else-if="previewAsset.fileType === 'image' && previewAsset.provider === 's3'" class="image-preview" :src="previewAsset.url" />
            <div v-else-if="previewAsset.fileType === 'subtitle'" class="subtitle-preview">
              字幕文件已上传：{{ previewAsset.originalFilename }}。后续可接字幕解析和在线查看。
            </div>
            <div v-else class="mock-preview">
              {{ previewAsset.fileType === 'video' ? '视频' : '图片' }}素材占位：{{ previewAsset.objectKey }}
            </div>
          </n-card>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { completeMediaUpload, getMediaAssets, presignMedia } from '../api/media'
import EpisodePicker from '../components/EpisodePicker.vue'
import ProjectPicker from '../components/ProjectPicker.vue'
import type { ShortDramaEpisode } from '../types/episode'
import type { MediaAsset, MediaPresignResult } from '../types/media'
import type { ShortDramaProject } from '../types/project'

const message = useMessage()
const route = useRoute()
const router = useRouter()
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const assets = ref<MediaAsset[]>([])
const previewAsset = ref<MediaAsset | null>(null)
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatusText = ref('等待选择文件')
const selectedProjectId = ref<number | null>(null)
const episodeId = ref<number | null>(null)
const episodeNo = ref<number | null>(null)

const acceptTypes = '.mp4,.mov,.webm,.jpg,.jpeg,.png,.srt'
const progressStatus = computed(() => (uploadProgress.value >= 100 ? 'success' : 'default'))
const mediaContextText = computed(() =>
  episodeId.value
    ? '当前媒体资产将绑定到该分集，用于后续视频转码、字幕/配音文件管理和海外版本预览。'
    : '当前为项目级媒体资产视角，可查看或上传该项目下的媒体素材；选择分集后会绑定到具体 episode。',
)
const localizedAssetBindText = computed(() =>
  episodeId.value
    ? `当前媒体资产将绑定到第 ${episodeNo.value || '-'} 集，用于后续视频转码、字幕/配音文件管理和海外版本预览。`
    : '当前为项目级媒体资产视角，建议从分集管理或本地化结果进入，以便素材沉淀到具体分集。',
)
const localizedAssetTypes = [
  { title: '原始视频', description: '用于后续转码和海外版本制作' },
  { title: '目标语言字幕', description: '由本地化结果导出或人工上传 SRT/VTT' },
  { title: '目标语言配音', description: '后续可接 TTS 或人工配音文件' },
  { title: '口型匹配视频', description: '后续可接第三方 lip-sync 服务生成' },
  { title: '海外预览成片', description: '用于审核和投放前预览' },
]

function clearPreviewAsset() {
  previewAsset.value = null
}

function handleProjectChange(_project: ShortDramaProject | null) {
  clearPreviewAsset()
  loadAssets({ autoPreview: false })
}

function handleEpisodeChange(episode: ShortDramaEpisode | null) {
  episodeId.value = episode?.id || null
  episodeNo.value = episode?.episode_no || null
  clearPreviewAsset()
  loadAssets({ autoPreview: false })
}

const columns: DataTableColumns<MediaAsset> = [
  { title: '文件名', key: 'originalFilename', minWidth: 180 },
  { title: '集数', key: 'episode_no', width: 90, render: (row) => row.episode_no ? `第 ${row.episode_no} 集` : '-' },
  { title: '分集 ID', key: 'episode_id', width: 90, render: (row) => row.episode_id || '-' },
  {
    title: '类型',
    key: 'fileType',
    width: 90,
    render: (row) => h(NTag, { type: row.fileType === 'video' ? 'info' : row.fileType === 'image' ? 'success' : 'warning', bordered: false }, { default: () => row.fileType }),
  },
  { title: '大小', key: 'size', width: 110, render: (row) => formatSize(row.size) },
  { title: '状态', key: 'status', width: 110, render: (row) => h(NTag, { type: row.status === 'uploaded' ? 'success' : 'warning', bordered: false }, { default: () => row.status }) },
  { title: 'Provider', key: 'provider', width: 100 },
  { title: '创建时间', key: 'createdAt', width: 170, render: (row) => new Date(row.createdAt).toLocaleString() },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => h(NButton, { size: 'small', secondary: true, onClick: () => (previewAsset.value = row) }, { default: () => row.fileType === 'subtitle' ? '查看' : '预览' }),
  },
]

function normalizeMimeType(file: File) {
  // srt 文件在部分浏览器中 file.type 为空，这里按扩展名补齐。
  if (file.type) return file.type
  if (file.name.toLowerCase().endsWith('.srt')) return 'application/x-subrip'
  return 'text/plain'
}

function formatSize(size: number) {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${(size / 1024).toFixed(1)} KB`
}

function validateFile(file: File) {
  const mimeType = normalizeMimeType(file)
  const isVideo = mimeType.startsWith('video/')
  const isImage = mimeType.startsWith('image/')
  const isSubtitle = mimeType === 'application/x-subrip' || mimeType === 'text/plain'

  if (!isVideo && !isImage && !isSubtitle) return '不支持的文件类型'
  if (isVideo && file.size > 500 * 1024 * 1024) return '视频文件不能超过 500MB'
  if (isImage && file.size > 20 * 1024 * 1024) return '图片文件不能超过 20MB'
  if (isSubtitle && file.size > 5 * 1024 * 1024) return '字幕文件不能超过 5MB'
  return ''
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const error = validateFile(file)
  if (error) {
    message.warning(error)
    input.value = ''
    return
  }

  selectedFile.value = file
  uploadProgress.value = 0
  uploadStatusText.value = '文件已选择，等待上传'
}

function putToS3(uploadUrl: string, file: File, contentType: string) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', uploadUrl)
    // S3 presigned PUT 不能额外带 Authorization，只保留签名时匹配的 Content-Type。
    xhr.setRequestHeader('Content-Type', contentType)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        uploadProgress.value = Math.round((event.loaded / event.total) * 100)
        uploadStatusText.value = `上传中 ${uploadProgress.value}%`
      }
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve()
      else reject(new Error(`S3 上传失败：${xhr.status}`))
    }
    xhr.onerror = () => reject(new Error('网络错误，上传失败'))
    xhr.send(file)
  })
}

async function mockUploadProgress() {
  // mock 模式不传文件，只模拟与真实上传一致的进度反馈。
  uploadStatusText.value = 'mock 上传模拟中'
  for (const value of [15, 35, 55, 78, 100]) {
    await new Promise((resolve) => window.setTimeout(resolve, 180))
    uploadProgress.value = value
  }
}

async function finishUpload(presign: MediaPresignResult) {
  const response = await completeMediaUpload({
    assetId: presign.assetId,
    objectKey: presign.objectKey,
    project_id: selectedProjectId.value,
    episode_id: episodeId.value,
    episode_no: episodeNo.value,
  })
  if (response.code === 0) {
    previewAsset.value = response.data
    uploadStatusText.value = '上传完成，素材记录已保存'
    message.success(selectedProjectId.value ? '媒体资产已归属到当前短剧项目。' : '素材上传完成')
    await loadAssets()
  }
}

async function handleUpload() {
  if (!selectedFile.value) return
  if (!selectedProjectId.value) {
    message.warning('建议选择短剧项目，方便沉淀到完整生产链路。')
  }
  if (!episodeId.value) {
    message.warning('请选择具体分集，媒体资产需要归属到对应集数。')
    return
  }
  uploading.value = true
  uploadProgress.value = 0
  try {
    const file = selectedFile.value
    const mimeType = normalizeMimeType(file)
    const response = await presignMedia({
      filename: file.name,
      mimeType,
      size: file.size,
      project_id: selectedProjectId.value,
      episode_id: episodeId.value,
      episode_no: episodeNo.value,
    })
    if (response.code !== 0) return

    if (response.data.provider === 'mock') await mockUploadProgress()
    else await putToS3(response.data.uploadUrl, file, mimeType)

    await finishUpload(response.data)
  } catch (error) {
    uploadStatusText.value = '上传失败'
    message.error(error instanceof Error ? error.message : '上传失败')
  } finally {
    uploading.value = false
  }
}

async function loadAssets(options: { autoPreview?: boolean } = {}) {
  const autoPreview = options.autoPreview ?? true
  loading.value = true
  try {
    const response = await getMediaAssets({
    project_id: selectedProjectId.value || undefined,
    episode_id: episodeId.value || undefined,
    episode_no: episodeNo.value || undefined,
  })
    if (response.code === 0) {
      assets.value = response.data
      if (!autoPreview) {
        clearPreviewAsset()
      } else {
        if (!previewAsset.value && response.data.length) previewAsset.value = response.data[0]
        if (previewAsset.value && selectedProjectId.value && previewAsset.value.project_id !== selectedProjectId.value) previewAsset.value = response.data[0] || null
        if (previewAsset.value && episodeId.value && previewAsset.value.episode_id !== episodeId.value) previewAsset.value = response.data[0] || null
      }
    }
  } catch {
    message.error('短剧项目列表加载失败')
  } finally {
    loading.value = false
  }
}

function loadEpisodeQuery() {
  // 从分集列表进入时会携带 episodeId / episodeNo；没有这些参数时媒体资产页保持独立可用。
  const queryEpisodeId = Number(route.query.episodeId)
  const queryEpisodeNo = Number(route.query.episodeNo)
  episodeId.value = queryEpisodeId || null
  episodeNo.value = queryEpisodeNo || null
}

onMounted(async () => {
  loadEpisodeQuery()
  // 从项目详情页或分集列表进入时，ProjectPicker 会根据 projectId 加载并回显项目详情。
  const queryProjectId = Number(route.query.projectId)
  if (queryProjectId) selectedProjectId.value = queryProjectId
  await loadAssets()
})
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.upload-note {
  margin-bottom: 16px;
}

.context-note {
  margin-bottom: 16px;
}

.localized-assets-card {
  margin-bottom: 16px;
  background: #fbfcff;
}

.localized-assets-copy {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.7;
}

.localized-bind-alert {
  margin: 10px 0 12px;
}

.localized-asset-types {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.localized-asset-type {
  min-height: 78px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
}

.localized-asset-title {
  color: #111827;
  font-weight: 800;
}

.localized-asset-desc {
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.55;
}

.project-back-btn {
  margin-bottom: 16px;
}

.episode-context-card {
  margin-bottom: 14px;
  background: #f8fafc;
}

.episode-context-title {
  color: #111827;
  font-weight: 800;
}

.episode-context-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin: 8px 0 12px;
  color: #6b7280;
  font-size: 12px;
}

.full-width {
  width: 100%;
}

.upload-box {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  text-align: center;
}

.file-input {
  display: none;
}

.upload-hint,
.file-meta,
.upload-status {
  color: #6b7280;
  font-size: 13px;
}

.file-card {
  display: grid;
  gap: 12px;
  margin-top: 16px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
}

.file-name {
  color: #111827;
  font-weight: 800;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.asset-card {
  min-height: 720px;
}

.preview-card {
  margin-top: 16px;
  background: #fbfcff;
}

.preview-alert {
  margin-bottom: 12px;
}

.media-preview,
.image-preview {
  width: 100%;
  max-height: 520px;
  border-radius: 8px;
  background: #111827;
  object-fit: contain;
}

.subtitle-preview,
.mock-preview {
  padding: 20px;
  color: #374151;
  border-radius: 8px;
  background: #f7f8fa;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
</style>
