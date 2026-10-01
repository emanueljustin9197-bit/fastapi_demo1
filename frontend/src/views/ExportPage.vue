<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiBaseUrl, apiFetch } from '../api/client'
import { questionnaireApi } from '../api/questionnaire'
import type { Questionnaire } from '../types'

type ExportFormat = 'csv' | 'xlsx' | 'json'
type ExportTask = {
  id: number
  questionnaireId?: number
  questionnaireTitle?: string
  format?: ExportFormat
  status?: string
  fileName?: string
  rowCount?: number
  createdAt?: string
  errorMessage?: string
}

const props = defineProps<{ token: string }>()
const questionnaireId = ref<number | null>(null)
const format = ref<ExportFormat>('xlsx')
const range = ref('all')
const includeMetadata = ref(true)
const items = ref<Questionnaire[]>([])
const tasks = ref<ExportTask[]>([])
const message = ref('')
const error = ref('')
const loading = ref(false)
const loadingTasks = ref(false)

const completeCount = computed(() => tasks.value.filter((item) => item.status === 'completed').length)
const selectedName = computed(() => items.value.find((item) => item.id === questionnaireId.value)?.title || '')
const formats: Array<{ value: ExportFormat; title: string; description: string }> = [
  { value: 'xlsx', title: 'Excel', description: '适合整理和二次分析' },
  { value: 'csv', title: 'CSV', description: '适合数据工具导入' },
  { value: 'json', title: 'JSON', description: '适合系统接口处理' },
]

function statusText(status?: string) {
  return ({ completed: '已完成', processing: '处理中', pending: '排队中', failed: '导出失败' } as Record<string, string>)[status || ''] || '等待处理'
}

function formatDate(value?: string) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function load() {
  loadingTasks.value = true
  error.value = ''
  try {
    const [questionnaires, exportData] = await Promise.all([
      questionnaireApi.list({ page: 1, pageSize: 100 }, props.token),
      apiFetch<{ list: ExportTask[] }>('/api/export/list?page=1&pageSize=10', {}, props.token),
    ])
    items.value = questionnaires.list
    tasks.value = exportData.list || []
  } catch (loadError) {
    error.value = (loadError as Error).message
  } finally {
    loadingTasks.value = false
  }
}

async function create() {
  message.value = ''
  error.value = ''
  if (!questionnaireId.value) {
    error.value = '请先选择需要导出的表格'
    return
  }
  loading.value = true
  try {
    const result = await apiFetch<{ id: number }>('/api/export/create', {
      method: 'POST',
      body: JSON.stringify({
        questionnaireId: questionnaireId.value,
        format: format.value,
        range: range.value,
        includeMetadata: includeMetadata.value,
      }),
    }, props.token)
    message.value = `导出任务 #${result.id} 已创建，完成后可在下方下载。`
    await load()
  } catch (createError) {
    error.value = (createError as Error).message
  } finally {
    loading.value = false
  }
}

async function download(task: ExportTask) {
  try {
    const response = await fetch(`${apiBaseUrl}/api/export/download?id=${task.id}`, {
      headers: { Authorization: `Bearer ${props.token}` },
    })
    if (!response.ok) throw new Error('下载文件失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = task.fileName || `export-${task.id}.${task.format || 'xlsx'}`
    link.click()
    URL.revokeObjectURL(url)
  } catch (downloadError) {
    error.value = (downloadError as Error).message
  }
}

async function remove(task: ExportTask) {
  if (!confirm('确定删除这条导出记录吗？')) return
  try {
    await apiFetch<null>(`/api/export/delete?id=${task.id}`, { method: 'DELETE' }, props.token)
    tasks.value = tasks.value.filter((item) => item.id !== task.id)
  } catch (removeError) {
    error.value = (removeError as Error).message
  }
}

onMounted(load)
</script>

<template>
  <header class="page-header export-heading">
    <div><h1>数据导出中心</h1><p>按需导出答卷数据，所有导出记录都保留在这里</p></div>
    <button :disabled="loadingTasks" class="refresh-button" title="刷新导出记录" @click="load">刷新</button>
  </header>

  <div class="export-overview">
    <div class="export-metric"><span>支持格式</span><strong>3</strong><small>Excel · CSV · JSON</small></div>
    <div class="export-metric"><span>最近导出</span><strong>{{ tasks.length }}</strong><small>最近 10 条任务</small></div>
    <div class="export-metric"><span>可下载文件</span><strong>{{ completeCount }}</strong><small>已处理完成</small></div>
  </div>

  <div v-if="error" class="error export-message">{{ error }}</div>
  <div v-if="message" class="export-message success-message">{{ message }}</div>

  <div class="export-layout">
    <section class="card export-builder">
      <div class="section-title"><div><h2>新建导出任务</h2><p>选择数据范围和文件格式，后台会生成可下载文件</p></div></div>
      <label class="export-field">选择表格
        <select v-model="questionnaireId">
          <option :value="null" disabled>请选择要导出的表格</option>
          <option v-for="item in items" :key="item.id" :value="item.id">{{ item.title }}{{ item.responseCount ? ` (${item.responseCount} 份答卷)` : '' }}</option>
        </select>
      </label>
      <p v-if="selectedName" class="selected-survey">当前选择：<strong>{{ selectedName }}</strong></p>
      <div class="export-label">导出格式</div>
      <div class="format-options">
        <button v-for="item in formats" :key="item.value" type="button" :class="{ selected: format === item.value }" @click="format = item.value">
          <b>{{ item.title }}</b><small>{{ item.description }}</small>
        </button>
      </div>
      <div class="export-label">数据范围</div>
      <div class="range-options">
        <button type="button" :class="{ selected: range === 'all' }" @click="range = 'all'">全部答卷</button>
        <button type="button" :class="{ selected: range === 'week' }" @click="range = 'week'">近 7 天</button>
        <button type="button" :class="{ selected: range === 'month' }" @click="range = 'month'">近 30 天</button>
      </div>
      <label class="metadata-option"><input v-model="includeMetadata" type="checkbox" /><span><b>包含答卷元数据</b><small>导出提交时间、来源等辅助字段</small></span></label>
      <button class="primary create-export" :disabled="loading" @click="create">{{ loading ? '正在创建任务...' : '创建导出任务' }}</button>
    </section>

    <aside class="export-guide">
      <div class="guide-icon">↓</div>
      <h2>导出更有条理</h2>
      <p>Excel 适合直接查看，CSV 和 JSON 便于导入其他分析工具。</p>
      <div><span>文件生成后会显示在右侧记录中</span><span>可随时下载或删除历史文件</span></div>
    </aside>
  </div>

  <section class="card export-history">
    <div class="history-head"><div><h2>导出记录</h2><p>最近创建的文件任务</p></div><span>{{ tasks.length }} 条记录</span></div>
    <div v-if="loadingTasks" class="empty">正在加载导出记录...</div>
    <div v-else-if="!tasks.length" class="empty export-empty"><b>还没有导出记录</b><span>创建第一个任务后，文件状态会在这里更新。</span></div>
    <div v-else class="export-table-wrap"><table class="export-table"><thead><tr><th>表格与文件</th><th>格式</th><th>答卷数</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead><tbody>
      <tr v-for="task in tasks" :key="task.id"><td><strong>{{ task.questionnaireTitle || `表格 #${task.questionnaireId || '-'}` }}</strong><small>{{ task.fileName || '文件生成中' }}</small></td><td><span class="format-tag">{{ (task.format || 'xlsx').toUpperCase() }}</span></td><td>{{ task.rowCount ?? '-' }}</td><td><span class="task-status" :class="task.status"><i></i>{{ statusText(task.status) }}</span><small v-if="task.errorMessage" class="task-error">{{ task.errorMessage }}</small></td><td>{{ formatDate(task.createdAt) }}</td><td class="export-actions"><button v-if="task.status === 'completed'" title="下载文件" @click="download(task)">下载</button><button class="danger" title="删除记录" @click="remove(task)">删除</button></td></tr>
    </tbody></table></div>
  </section>
</template>
