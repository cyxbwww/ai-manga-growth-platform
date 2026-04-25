<template>
  <div class="module-page">
    <n-grid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <n-grid-item :span="8" :s-span="24">
        <n-space vertical size="large">
          <n-card title="素材上传" :bordered="false">
            <n-alert type="info" :bordered="false" class="upload-note">
              前端选择文件后，先向后端获取 S3 presigned URL，再由浏览器直传 S3；FastAPI 只保存素材元数据。
            </n-alert>

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
            <n-button size="small" secondary @click="loadAssets">刷新</n-button>
          </template>

          <n-data-table :columns="columns" :data="assets" :bordered="false" :single-line="false" />

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
import { NButton, NTag, useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { completeMediaUpload, getMediaAssets, presignMedia } from '../api/media'
import type { MediaAsset, MediaPresignResult } from '../types/media'

const message = useMessage()
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const assets = ref<MediaAsset[]>([])
const previewAsset = ref<MediaAsset | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatusText = ref('等待选择文件')

const acceptTypes = '.mp4,.mov,.webm,.jpg,.jpeg,.png,.srt'
const progressStatus = computed(() => (uploadProgress.value >= 100 ? 'success' : 'default'))

const columns: DataTableColumns<MediaAsset> = [
  { title: '文件名', key: 'originalFilename', minWidth: 180 },
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
  const response = await completeMediaUpload({ assetId: presign.assetId, objectKey: presign.objectKey })
  if (response.code === 0) {
    previewAsset.value = response.data
    uploadStatusText.value = '上传完成，素材记录已保存'
    message.success('素材上传完成')
    await loadAssets()
  }
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadProgress.value = 0
  try {
    const file = selectedFile.value
    const mimeType = normalizeMimeType(file)
    const response = await presignMedia({ filename: file.name, mimeType, size: file.size })
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

async function loadAssets() {
  const response = await getMediaAssets()
  if (response.code === 0) {
    assets.value = response.data
    if (!previewAsset.value && response.data.length) previewAsset.value = response.data[0]
  }
}

onMounted(loadAssets)
</script>

<style scoped>
.module-page {
  min-height: calc(100vh - 120px);
}

.upload-note {
  margin-bottom: 16px;
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
</style>
