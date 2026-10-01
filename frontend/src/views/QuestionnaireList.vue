<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { questionnaireApi } from '../api/questionnaire'
import type { Questionnaire } from '../types'

const props = defineProps<{ token: string }>()
const emit = defineEmits<{ create: []; edit: [number]; analyze: [number] }>()
const items = ref<Questionnaire[]>([])
const keyword = ref('')
const status = ref('')
const loading = ref(false)
const error = ref('')
const stats = ref<Record<string, number>>({
  questionnaireCount: 0,
  responseCount: 0,
  activeCount: 0,
  averageCompletionRate: 0,
})

function editItem(item: Questionnaire) {
  if (item.id !== undefined) emit('edit', item.id)
}

function analyzeItem(item: Questionnaire) {
  if (item.id !== undefined) emit('analyze', item.id)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [result, summary] = await Promise.all([
      questionnaireApi.list({
        keyword: keyword.value,
        status: status.value,
        page: 1,
        pageSize: 20,
      }, props.token),
      questionnaireApi.statistics(props.token),
    ])
    items.value = result.list
    stats.value = summary
  } catch (loadError) {
    error.value = (loadError as Error).message
  } finally {
    loading.value = false
  }
}

async function action(kind: 'delete' | 'copy' | 'publish' | 'close', item: Questionnaire) {
  if (!item.id) return
  if (kind === 'delete' && !confirm('确定删除这份表格吗？')) return
  try {
    if (kind === 'delete') await questionnaireApi.remove(item.id, props.token)
    if (kind === 'copy') await questionnaireApi.copy(item.id, props.token)
    if (kind === 'publish') await questionnaireApi.publish(item.id, props.token)
    if (kind === 'close') await questionnaireApi.close(item.id, props.token)
    await load()
  } catch (actionError) {
    error.value = (actionError as Error).message
  }
}

onMounted(load)
</script>

<template>
  <header class="page-header">
    <div>
      <h1>我的表格</h1>
      <p>管理已创建的表格</p>
    </div>
    <button class="primary" @click="emit('create')">＋ 新建表格</button>
  </header>

  <div class="stats-grid">
    <div class="stat-card"><b>{{ stats.questionnaireCount || 0 }}</b><span>表格总数</span></div>
    <div class="stat-card"><b>{{ stats.responseCount || 0 }}</b><span>累计回收</span></div>
    <div class="stat-card"><b>{{ stats.activeCount || 0 }}</b><span>正在收集</span></div>
    <div class="stat-card"><b>{{ stats.averageCompletionRate || 0 }}%</b><span>平均完成率</span></div>
  </div>

  <section class="card list-card">
    <div class="toolbar">
      <input v-model="keyword" placeholder="搜索表格名称" @keyup.enter="load" />
      <select v-model="status" @change="load">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="active">正在收集</option>
        <option value="closed">已关闭</option>
      </select>
      <button @click="load">搜索</button>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="loading" class="empty">正在加载...</div>
    <div v-else-if="!items.length" class="empty">暂无表格</div>
    <table v-else>
      <thead>
        <tr><th>表格名称</th><th>回收答卷</th><th>完成率</th><th>状态</th><th>最后更新</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td><strong>{{ item.title }}</strong><small>{{ item.questionCount || item.questions?.length || 0 }} 道题目</small></td>
          <td>{{ item.responseCount || 0 }}</td>
          <td>{{ item.completionRate || 0 }}%</td>
          <td>
            <span class="badge" :class="item.status">
              {{ item.status === 'active' ? '收集中' : item.status === 'closed' ? '已关闭' : '草稿' }}
            </span>
          </td>
          <td>{{ item.updatedAt ? new Date(item.updatedAt).toLocaleDateString() : '-' }}</td>
          <td class="actions">
            <button @click="editItem(item)">编辑</button>
            <button @click="analyzeItem(item)">分析</button>
            <button v-if="item.status === 'draft'" @click="action('publish', item)">发布</button>
            <button v-if="item.status === 'active'" @click="action('close', item)">停止</button>
            <button @click="action('copy', item)">复制</button>
            <button class="danger" @click="action('delete', item)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
