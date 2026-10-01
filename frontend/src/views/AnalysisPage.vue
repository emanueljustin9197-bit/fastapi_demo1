<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  analysisApi,
  type AnalysisChannel,
  type AnalysisChannelSource,
  type AnalysisTrendPoint,
} from '../api/analysis'
import { apiFetch } from '../api/client'
import { questionnaireApi } from '../api/questionnaire'
import { responseApi, type ResponseDetail, type ResponseSummary } from '../api/response'
import type { Questionnaire } from '../types'

type TimeRange = '7d' | '30d'

interface AiEvidence {
  sourceType: 'overview' | 'trend' | 'question'
  sourceId: string
  text: string
}

interface AiFinding {
  conclusion: string
  evidence: AiEvidence[]
}

interface AiInsight {
  findings: AiFinding[]
  suggestions: string[]
}

interface AiChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  evidence: AiEvidence[]
}

interface AiChatResponse {
  conversationId: string
  answer: string
  evidence: AiEvidence[]
}

interface AnomalyResponse {
  id: number
  respondentName?: string | null
  respondentEmail?: string | null
  durationSeconds: number
  submittedAt: string
  isValid: boolean
  riskScore: number
  riskReasons: string[]
  reviewStatus: 'pending' | 'confirmed' | 'dismissed'
}

interface UserFeedback {
  id: number
  responseId: number
  rating: number
  issueType: string
  content?: string | null
  createdAt: string
}

interface FeedbackResult {
  total: number
  averageRating: number
  issueCount: number
  list: UserFeedback[]
}

const props = defineProps<{ token: string; questionnaireId: number | null }>()
const questionnaires = ref<Questionnaire[]>([])
const selectedQuestionnaireId = ref<number | null>(props.questionnaireId)
const overview = ref<Record<string, number>>({})
const questions = ref<any[]>([])
const responses = ref<ResponseSummary[]>([])
const trend = ref<AnalysisTrendPoint[]>([])
const channels = ref<AnalysisChannel[]>([])
const detail = ref<ResponseDetail | null>(null)
const timeRange = ref<TimeRange>('7d')
const error = ref('')
const loading = ref(false)
const trendLoading = ref(false)
const channelsLoading = ref(false)
const aiLoading = ref(false)
const aiInsight = ref<AiInsight | null>(null)
const aiError = ref('')
const aiQuestion = ref('')
const aiChatLoading = ref(false)
const aiMessages = ref<AiChatMessage[]>([])
const conversationId = ref(createConversationId())
const selectorLoading = ref(false)
const questionsExpanded = ref(false)
const anomalies = ref<AnomalyResponse[]>([])
const anomaliesLoading = ref(false)
const anomaliesError = ref('')
const anomalyFilter = ref<'all' | 'pending' | 'confirmed'>('all')
const reviewingResponseId = ref<number | null>(null)
const feedback = ref<FeedbackResult>({ total: 0, averageRating: 0, issueCount: 0, list: [] })
const feedbackLoading = ref(false)
const feedbackError = ref('')

const trendMax = computed(() => Math.max(...trend.value.map((item) => item.count), 1))
const trendTotal = computed(() => trend.value.reduce((total, item) => total + item.count, 0))
const selectedQuestionnaire = computed(() => questionnaires.value.find(
  (item) => item.id === selectedQuestionnaireId.value,
))
const filteredAnomalies = computed(() => anomalyFilter.value === 'all'
  ? anomalies.value
  : anomalies.value.filter((item) => item.reviewStatus === anomalyFilter.value))
const pendingAnomalyCount = computed(() => anomalies.value.filter(
  (item) => item.reviewStatus === 'pending',
).length)
const channelDefinitions: Array<{
  source: AnalysisChannelSource
  label: string
  mark: string
}> = [
  { source: 'publicLink', label: '公开链接', mark: '↗' },
  { source: 'qrCode', label: '二维码', mark: '▦' },
  { source: 'wechat', label: '微信转发', mark: '微' },
]
const channelTotal = computed(() => channels.value.reduce((total, item) => total + item.count, 0))
const channelRows = computed(() => channelDefinitions.map((definition) => {
  const channel = channels.value.find((item) => item.source === definition.source)
  const count = channel?.count || 0
  return {
    ...definition,
    count,
    percentage: channelTotal.value ? Math.round(count / channelTotal.value * 1000) / 10 : 0,
  }
}))

function createConversationId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function startNewConversation() {
  conversationId.value = createConversationId()
  aiMessages.value = []
  aiQuestion.value = ''
  aiError.value = ''
}

async function clearConversation() {
  const questionnaireId = selectedQuestionnaireId.value
  const currentConversationId = conversationId.value
  aiChatLoading.value = true
  try {
    if (questionnaireId && aiMessages.value.length) {
      await apiFetch('/api/ai/analysis/chat/clear', {
        method: 'POST',
        body: JSON.stringify({
          questionnaireId,
          conversationId: currentConversationId,
        }),
      }, props.token)
    }
  } catch {
    // A new local conversation remains available before the clear endpoint is deployed.
  } finally {
    startNewConversation()
    aiChatLoading.value = false
  }
}

const chart = {
  width: 800,
  height: 220,
  left: 42,
  right: 16,
  top: 18,
  bottom: 34,
}
const chartPlotWidth = chart.width - chart.left - chart.right
const chartPlotHeight = chart.height - chart.top - chart.bottom
const trendCoordinates = computed(() => trend.value.map((item, index) => ({
  ...item,
  x: chart.left + (trend.value.length <= 1 ? chartPlotWidth / 2 : index / (trend.value.length - 1) * chartPlotWidth),
  y: chart.top + chartPlotHeight - item.count / trendMax.value * chartPlotHeight,
  showLabel: trend.value.length <= 14 || index % 5 === 0 || index === trend.value.length - 1,
})))
const trendLinePoints = computed(() => trendCoordinates.value.map((point) => `${point.x},${point.y}`).join(' '))
const trendTicks = computed(() => [trendMax.value, trendMax.value / 2, 0].map((value, index) => ({
  value: Number.isInteger(value) ? String(value) : value.toFixed(1),
  y: chart.top + index * chartPlotHeight / 2,
})))
function rangeText(range: TimeRange) {
  return range === '7d' ? '最近 7 天' : '最近 30 天'
}

function rangeDays(range: TimeRange) {
  return range === '7d' ? 7 : 30
}

function fallbackTrend(): AnalysisTrendPoint[] {
  const days = rangeDays(timeRange.value)
  const now = new Date()
  const slots = Array.from({ length: days }, (_, index) => {
    const date = new Date(now)
    date.setHours(0, 0, 0, 0)
    date.setDate(now.getDate() - (days - 1 - index))
    return { date, count: 0 }
  })
  const slotMap = new Map(slots.map((item) => [item.date.toISOString().slice(0, 10), item]))
  responses.value.forEach((response) => {
    const date = new Date(response.submittedAt)
    const key = Number.isNaN(date.getTime()) ? '' : date.toISOString().slice(0, 10)
    const slot = slotMap.get(key)
    if (slot) slot.count += 1
  })
  return slots.map((item) => ({
    date: item.date.toISOString().slice(0, 10),
    label: days > 14 ? `${item.date.getMonth() + 1}/${item.date.getDate()}` : `${item.date.getMonth() + 1}.${item.date.getDate()}`,
    count: item.count,
  }))
}

function normalizeTrend(items: AnalysisTrendPoint[]): AnalysisTrendPoint[] {
  return items.map((item) => {
    const date = item.date ? new Date(`${item.date}T00:00:00`) : null
    return {
      ...item,
      label: item.label || (date && !Number.isNaN(date.getTime())
        ? `${date.getMonth() + 1}.${date.getDate()}`
        : '-'),
    }
  })
}

async function loadTrend() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  trendLoading.value = true
  try {
    trend.value = normalizeTrend(
      await analysisApi.trend(questionnaireId, rangeDays(timeRange.value), props.token),
    )
  } catch {
    trend.value = fallbackTrend()
  } finally {
    trendLoading.value = false
  }
}

function fallbackChannels(): AnalysisChannel[] {
  const counts = new Map<AnalysisChannelSource, number>()
  responses.value.forEach((response) => {
    if (response.source === 'publicLink' || response.source === 'qrCode' || response.source === 'wechat') {
      counts.set(response.source, (counts.get(response.source) || 0) + 1)
    }
  })
  const total = responses.value.length
  return channelDefinitions.map((definition) => {
    const count = counts.get(definition.source) || 0
    return {
      source: definition.source,
      label: definition.label,
      count,
      percentage: total ? Math.round(count / total * 1000) / 10 : 0,
    }
  })
}

async function loadChannels() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  channelsLoading.value = true
  try {
    channels.value = await analysisApi.channels(questionnaireId, props.token)
  } catch {
    channels.value = fallbackChannels()
  } finally {
    channelsLoading.value = false
  }
}

async function loadAnomalies() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  anomaliesLoading.value = true
  anomaliesError.value = ''
  try {
    const result = await apiFetch<{ list: AnomalyResponse[]; total: number }>(
      `/api/response/anomalies?questionnaireId=${questionnaireId}`,
      {},
      props.token,
    )
    anomalies.value = result.list
  } catch (loadError) {
    anomalies.value = []
    anomaliesError.value = (loadError as Error).message
  } finally {
    anomaliesLoading.value = false
  }
}

async function scanAnomalies() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  anomaliesLoading.value = true
  anomaliesError.value = ''
  try {
    await apiFetch('/api/response/anomalies/scan', {
      method: 'POST',
      body: JSON.stringify({ questionnaireId }),
    }, props.token)
    await loadAnomalies()
  } catch (scanError) {
    anomaliesError.value = (scanError as Error).message
  } finally {
    anomaliesLoading.value = false
  }
}

async function loadFeedback() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  feedbackLoading.value = true
  feedbackError.value = ''
  try {
    feedback.value = await apiFetch<FeedbackResult>(
      `/api/feedback/list?questionnaireId=${questionnaireId}`,
      {},
      props.token,
    )
  } catch (loadError) {
    feedback.value = { total: 0, averageRating: 0, issueCount: 0, list: [] }
    feedbackError.value = (loadError as Error).message
  } finally {
    feedbackLoading.value = false
  }
}

async function load() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  loading.value = true
  error.value = ''
  try {
    const [overviewResult, questionResult, responseResult] = await Promise.all([
      analysisApi.overview(questionnaireId, props.token),
      analysisApi.questions(questionnaireId, props.token),
      responseApi.list(questionnaireId, props.token),
    ])
    overview.value = overviewResult as Record<string, number>
    questions.value = questionResult
    responses.value = responseResult.list
    await Promise.all([loadTrend(), loadChannels(), loadAnomalies(), loadFeedback()])
  } catch (loadError) {
    error.value = (loadError as Error).message
  } finally {
    loading.value = false
  }
}

async function loadQuestionnaires() {
  selectorLoading.value = true
  try {
    const result = await questionnaireApi.list({ page: 1, pageSize: 100 }, props.token)
    questionnaires.value = result.list
    const selectedExists = result.list.some((item) => item.id === selectedQuestionnaireId.value)
    if (!selectedExists) {
      selectedQuestionnaireId.value = result.list.find((item) => item.status === 'active')?.id
        || result.list[0]?.id
        || null
    }
  } catch (loadError) {
    error.value = (loadError as Error).message
  } finally {
    selectorLoading.value = false
  }
}

async function changeQuestionnaire() {
  overview.value = {}
  questions.value = []
  responses.value = []
  trend.value = []
  channels.value = []
  detail.value = null
  aiInsight.value = null
  aiError.value = ''
  questionsExpanded.value = false
  anomalies.value = []
  anomaliesError.value = ''
  anomalyFilter.value = 'all'
  feedback.value = { total: 0, averageRating: 0, issueCount: 0, list: [] }
  feedbackError.value = ''
  startNewConversation()
  await load()
}

async function changeRange(range: TimeRange) {
  timeRange.value = range
  aiInsight.value = null
  aiError.value = ''
  startNewConversation()
  await loadTrend()
}

async function generateInsight() {
  const questionnaireId = selectedQuestionnaireId.value
  if (!questionnaireId) return
  aiLoading.value = true
  aiError.value = ''
  try {
    const result = await apiFetch<AiInsight>('/api/ai/analysis/insight', {
      method: 'POST',
      body: JSON.stringify({
        questionnaireId,
        range: timeRange.value,
      }),
    }, props.token)
    aiInsight.value = result
  } catch (aiLoadError) {
    aiError.value = (aiLoadError as Error).message
  } finally {
    aiLoading.value = false
  }
}

async function askAi() {
  const questionnaireId = selectedQuestionnaireId.value
  const message = aiQuestion.value.trim()
  if (!questionnaireId || !message || aiChatLoading.value) return

  aiMessages.value.push({
    id: createConversationId(),
    role: 'user',
    content: message,
    evidence: [],
  })
  aiQuestion.value = ''
  aiChatLoading.value = true
  aiError.value = ''

  try {
    const result = await apiFetch<AiChatResponse>('/api/ai/analysis/chat', {
      method: 'POST',
      body: JSON.stringify({
        questionnaireId,
        range: timeRange.value,
        conversationId: conversationId.value,
        message,
      }),
    }, props.token)
    conversationId.value = result.conversationId
    aiMessages.value.push({
      id: createConversationId(),
      role: 'assistant',
      content: result.answer,
      evidence: result.evidence || [],
    })
  } catch (chatError) {
    aiError.value = (chatError as Error).message
  } finally {
    aiChatLoading.value = false
  }
}

async function showResponse(id: number) {
  try {
    detail.value = await responseApi.detail(id, props.token)
  } catch (loadError) {
    error.value = (loadError as Error).message
  }
}

async function updateValidity(item: AnomalyResponse, isValid: boolean) {
  reviewingResponseId.value = item.id
  anomaliesError.value = ''
  try {
    await apiFetch('/api/response/validity', {
      method: 'PUT',
      body: JSON.stringify({ responseId: item.id, isValid }),
    }, props.token)
    await load()
  } catch (updateError) {
    anomaliesError.value = (updateError as Error).message
  } finally {
    reviewingResponseId.value = null
  }
}

watch(() => props.questionnaireId, async (questionnaireId) => {
  if (!questionnaireId || questionnaireId === selectedQuestionnaireId.value) return
  selectedQuestionnaireId.value = questionnaireId
  await changeQuestionnaire()
})

onMounted(async () => {
  await loadQuestionnaires()
  await load()
})
</script>

<template>
  <header class="page-header analysis-heading">
    <div><h1>表格分析</h1><p>查看填写趋势、题目反馈与答卷明细</p></div>
    <div class="analysis-header-actions">
      <label class="analysis-questionnaire-select">
        <span>分析表格</span>
        <select v-model.number="selectedQuestionnaireId" :disabled="selectorLoading || !questionnaires.length" @change="changeQuestionnaire">
          <option v-if="!questionnaires.length" :value="null">{{ selectorLoading ? '正在加载...' : '暂无表格' }}</option>
          <option v-for="item in questionnaires" :key="item.id" :value="item.id">{{ item.title }}</option>
        </select>
      </label>
      <button :disabled="loading || !selectedQuestionnaireId" class="refresh-button" @click="load">刷新数据</button>
    </div>
  </header>
  <div v-if="!selectedQuestionnaireId" class="card empty">暂无可分析的表格，请先创建一份表格。</div>
  <template v-else>
    <div class="analysis-current-form"><span>当前分析</span><strong>{{ selectedQuestionnaire?.title || '已选择表格' }}</strong></div>
    <div class="stats-grid analysis-stats">
      <div class="stat-card"><b>{{ overview.responseCount || 0 }}</b><span>回收答卷</span></div>
      <div class="stat-card"><b>{{ overview.validResponseCount || 0 }}</b><span>有效答卷</span></div>
      <div class="stat-card"><b>{{ overview.averageDurationSeconds || 0 }} 秒</b><span>平均完成时间</span></div>
      <div class="stat-card"><b>{{ overview.completionRate || 0 }}%</b><span>完成率</span></div>
    </div>
    <div v-if="error" class="error analysis-error">{{ error }}</div>

    <div class="analysis-top-grid">
      <section class="card trend-card">
        <div class="trend-head"><div><h2>提交趋势</h2><p>{{ rangeText(timeRange) }}内累计 {{ trendTotal }} 份答卷</p></div><div class="range-tabs"><button v-for="item in ([['7d', '最近 7 天'], ['30d', '近一个月']] as Array<[TimeRange, string]>)" :key="item[0]" :class="{ active: timeRange === item[0] }" @click="changeRange(item[0])">{{ item[1] }}</button></div></div>
        <div v-if="trendLoading" class="trend-loading">正在汇总趋势数据...</div>
        <div v-else class="trend-line-chart">
          <svg :viewBox="`0 0 ${chart.width} ${chart.height}`" role="img" :aria-label="`${rangeText(timeRange)}提交趋势折线图`">
            <g v-for="tick in trendTicks" :key="tick.y">
              <line class="trend-grid-line" :x1="chart.left" :x2="chart.width - chart.right" :y1="tick.y" :y2="tick.y" />
              <text class="trend-y-label" :x="chart.left - 9" :y="tick.y + 4">{{ tick.value }}</text>
            </g>
            <polyline v-if="trendCoordinates.length" class="trend-line" :points="trendLinePoints" />
            <g v-for="point in trendCoordinates" :key="point.date || point.label" class="trend-point">
              <circle :cx="point.x" :cy="point.y" r="4"><title>{{ point.label }}：{{ point.count }} 份</title></circle>
              <text v-if="point.count" class="trend-value-label" :x="point.x" :y="point.y - 10">{{ point.count }}</text>
              <text v-if="point.showLabel" class="trend-x-label" :x="point.x" :y="chart.height - 8">{{ point.label }}</text>
            </g>
          </svg>
        </div>
      </section>

      <aside class="card channel-card">
        <div class="channel-head">
          <div><h2>问卷来源</h2><p>不同分享入口的答卷分布</p></div>
          <span>{{ channelTotal }} 份</span>
        </div>
        <div v-if="channelsLoading" class="channel-loading">正在汇总来源...</div>
        <div v-else class="channel-table" role="table" aria-label="问卷来源统计">
          <div class="channel-table-head" role="row">
            <span role="columnheader">来源</span>
            <span role="columnheader">答卷</span>
            <span role="columnheader">占比</span>
          </div>
          <div v-for="channel in channelRows" :key="channel.source" class="channel-row" role="row">
            <div class="channel-name" role="cell">
              <span :class="`channel-mark ${channel.source}`">{{ channel.mark }}</span>
              <strong>{{ channel.label }}</strong>
            </div>
            <b role="cell">{{ channel.count }}</b>
            <span role="cell">{{ channel.percentage }}%</span>
            <div class="channel-bar" aria-hidden="true"><i :style="{ width: `${channel.percentage}%` }"></i></div>
          </div>
        </div>
        <div class="channel-foot">
          <span>链接</span><span>扫码</span><span>微信内转发</span>
        </div>
      </aside>

      <aside class="ai-insight-card">
        <div class="ai-insight-header">
          <div class="ai-insight-identity">
            <div class="ai-insight-mark">AI</div>
            <div class="ai-title"><h2>AI 数据洞察</h2><span>DeepSeek · 基于当前表格数据生成</span></div>
          </div>
          <div class="ai-header-actions">
            <button v-if="aiMessages.length" class="ai-new-chat-button" :disabled="aiChatLoading" @click="clearConversation">新对话</button>
            <button class="ai-insight-button" :disabled="aiLoading" @click="generateInsight">{{ aiLoading ? '正在分析...' : aiInsight ? '重新生成洞察' : '生成 AI 分析' }}</button>
          </div>
        </div>
        <p v-if="!aiInsight" class="ai-insight-empty">基于答卷趋势、完成率和题目统计，生成一份包含关键发现、异常提示和改进建议的分析报告。</p>
        <div v-else class="ai-result">
          <div class="ai-report-label">分析报告</div>
          <section class="ai-report-section">
            <h3>关键发现</h3>
            <article v-for="(finding, index) in aiInsight.findings" :key="index" class="ai-finding">
              <div class="ai-finding-number">{{ index + 1 }}</div>
              <div>
                <p class="ai-conclusion">{{ finding.conclusion }}</p>
                <ul class="ai-evidence-list">
                  <li v-for="evidence in finding.evidence" :key="`${evidence.sourceType}-${evidence.sourceId}-${evidence.text}`">
                    <span>数据依据</span>{{ evidence.text }}
                  </li>
                </ul>
              </div>
            </article>
            <p v-if="!aiInsight.findings.length" class="ai-report-empty">当前数据不足以生成关键发现。</p>
          </section>
          <section class="ai-report-section ai-suggestions">
            <h3>改进建议</h3>
            <ol v-if="aiInsight.suggestions.length">
              <li v-for="suggestion in aiInsight.suggestions" :key="suggestion">{{ suggestion }}</li>
            </ol>
            <p v-else class="ai-report-empty">暂无改进建议。</p>
          </section>
        </div>
        <section class="ai-chat-panel">
          <div class="ai-chat-heading">
            <div><h3>追问数据</h3><span>连续对话 · {{ rangeText(timeRange) }}</span></div>
            <span v-if="aiMessages.length" class="ai-chat-count">{{ aiMessages.length }} 条消息</span>
          </div>
          <div v-if="aiMessages.length" class="ai-chat-messages" aria-live="polite">
            <article v-for="message in aiMessages" :key="message.id" :class="['ai-chat-message', message.role]">
              <span>{{ message.role === 'user' ? '你' : 'AI' }}</span>
              <div>
                <p>{{ message.content }}</p>
                <ul v-if="message.evidence.length" class="ai-chat-evidence">
                  <li v-for="evidence in message.evidence" :key="`${message.id}-${evidence.sourceType}-${evidence.sourceId}`">
                    {{ evidence.text }}
                  </li>
                </ul>
              </div>
            </article>
          </div>
          <p v-else class="ai-chat-empty">可以继续追问趋势变化、题目表现和改进方向。</p>
          <div class="ai-chat-composer">
            <textarea
              v-model="aiQuestion"
              rows="2"
              maxlength="500"
              placeholder="例如：完成率偏低可能和哪些题目有关？"
              :disabled="aiChatLoading"
              @keydown.enter.exact.prevent="askAi"
            />
            <button class="ai-chat-send" :disabled="aiChatLoading || !aiQuestion.trim()" @click="askAi">
              {{ aiChatLoading ? '分析中...' : '发送' }}
            </button>
          </div>
        </section>
        <div v-if="aiError" class="ai-error">{{ aiError }}</div>
      </aside>
    </div>

    <section class="card question-analysis-card">
      <button class="question-analysis-toggle" type="button" :aria-expanded="questionsExpanded" @click="questionsExpanded = !questionsExpanded">
        <span><strong>题目统计</strong><small>快速识别高选择项和被跳过的问题</small></span>
        <span class="question-toggle-meta">{{ questions.length }} 道题 <b :class="{ expanded: questionsExpanded }">⌄</b></span>
      </button>
      <div v-show="questionsExpanded" class="question-analysis-content">
        <div v-for="item in questions" :key="item.questionId" class="question-stat">
          <strong>{{ item.title }}</strong><span>{{ item.answerCount || 0 }} 人回答，{{ item.skipCount || 0 }} 人跳过</span>
          <div v-for="option in item.options || []" :key="option.optionId" class="bar-row"><label>{{ option.label }}</label><div class="bar"><i :style="{ width: `${option.percentage || 0}%` }"></i></div><em>{{ option.percentage || 0 }}%</em></div>
        </div>
        <div v-if="!questions.length" class="empty">暂无题目统计</div>
      </div>
    </section>

    <section class="card review-card">
      <div class="module-heading">
        <div>
          <h2>异常答卷审查</h2>
          <p>根据填写耗时、答案重复度和内容完整性识别疑似异常答卷</p>
        </div>
        <span class="module-count">{{ pendingAnomalyCount }} 份待审查</span>
      </div>
      <div class="review-toolbar">
        <div class="review-tabs" role="group" aria-label="异常答卷筛选">
          <button :class="{ active: anomalyFilter === 'all' }" @click="anomalyFilter = 'all'">全部</button>
          <button :class="{ active: anomalyFilter === 'pending' }" @click="anomalyFilter = 'pending'">待审查</button>
          <button :class="{ active: anomalyFilter === 'confirmed' }" @click="anomalyFilter = 'confirmed'">已确认无效</button>
        </div>
        <button :disabled="anomaliesLoading" @click="scanAnomalies">{{ anomaliesLoading ? '检测中...' : '重新检测' }}</button>
      </div>
      <div v-if="anomaliesError" class="module-error">{{ anomaliesError }}</div>
      <div v-if="anomaliesLoading && !anomalies.length" class="module-empty">正在检测异常答卷...</div>
      <div v-else-if="!filteredAnomalies.length" class="module-empty">当前筛选条件下没有异常答卷</div>
      <div v-else class="review-list">
        <article v-for="item in filteredAnomalies" :key="item.id" class="review-item">
          <div class="risk-score" :class="{ high: item.riskScore >= 60 }">
            <strong>{{ item.riskScore }}</strong><span>风险分</span>
          </div>
          <div class="review-content">
            <div class="review-title">
              <strong>答卷 #{{ item.id }}</strong>
              <span :class="['review-status', item.reviewStatus]">
                {{ item.reviewStatus === 'confirmed' ? '已确认无效' : item.reviewStatus === 'dismissed' ? '已恢复有效' : '待审查' }}
              </span>
            </div>
            <p>{{ item.respondentName || '匿名填写' }} · 用时 {{ item.durationSeconds }} 秒 · {{ new Date(item.submittedAt).toLocaleString() }}</p>
            <div class="risk-reasons">
              <span v-for="reason in item.riskReasons" :key="reason">{{ reason }}</span>
            </div>
          </div>
          <div class="review-actions">
            <button @click="showResponse(item.id)">查看答卷</button>
            <button
              v-if="item.isValid"
              class="danger"
              :disabled="reviewingResponseId === item.id"
              @click="updateValidity(item, false)"
            >标记无效</button>
            <button
              v-else
              :disabled="reviewingResponseId === item.id"
              @click="updateValidity(item, true)"
            >恢复有效</button>
          </div>
        </article>
      </div>
    </section>

    <section class="card feedback-card">
      <div class="module-heading">
        <div>
          <h2>填写体验反馈</h2>
          <p>汇总填写者在提交完成后留下的评分和问题反馈</p>
        </div>
        <button :disabled="feedbackLoading" @click="loadFeedback">{{ feedbackLoading ? '加载中...' : '刷新反馈' }}</button>
      </div>
      <div class="feedback-summary">
        <div><strong>{{ feedback.averageRating || 0 }}</strong><span>平均评分 / 5</span></div>
        <div><strong>{{ feedback.total }}</strong><span>反馈数量</span></div>
        <div><strong>{{ feedback.issueCount }}</strong><span>问题反馈</span></div>
      </div>
      <div v-if="feedbackError" class="module-error">{{ feedbackError }}</div>
      <div v-if="feedbackLoading && !feedback.list.length" class="module-empty">正在加载用户反馈...</div>
      <div v-else-if="!feedback.list.length" class="module-empty">暂无用户反馈</div>
      <div v-else class="feedback-list">
        <article v-for="item in feedback.list" :key="item.id" class="feedback-item">
          <div class="feedback-rating" :aria-label="`${item.rating} 分`">{{ '★'.repeat(item.rating) }}<span>{{ '★'.repeat(5 - item.rating) }}</span></div>
          <p>{{ item.content || '用户未填写文字反馈' }}</p>
          <small>答卷 #{{ item.responseId }} · {{ item.issueType === 'none' ? '无问题' : item.issueType }} · {{ new Date(item.createdAt).toLocaleString() }}</small>
        </article>
      </div>
    </section>

    <section class="card response-table-card">
      <div class="history-head"><div><h2>答卷明细</h2><p>查看单份提交的完整内容</p></div><span>{{ responses.length }} 份答卷</span></div>
      <div v-if="!responses.length" class="empty">暂无答卷</div>
      <div v-else class="export-table-wrap"><table><thead><tr><th>编号</th><th>填写者</th><th>来源</th><th>用时</th><th>提交时间</th><th></th></tr></thead><tbody><tr v-for="item in responses" :key="item.id"><td>#{{ item.id }}</td><td>{{ item.respondentName || '匿名' }}<small>{{ item.respondentEmail || '' }}</small></td><td>{{ item.source }}</td><td>{{ item.durationSeconds }} 秒</td><td>{{ new Date(item.submittedAt).toLocaleString() }}</td><td><button @click="showResponse(item.id)">查看回答</button></td></tr></tbody></table></div>
    </section>

    <div v-if="detail" class="modal-backdrop" @click.self="detail = null"><div class="modal"><button class="modal-close" @click="detail = null">×</button><h2>答卷 #{{ detail.id }}</h2><p v-if="detail.respondentName || detail.respondentEmail">{{ detail.respondentName || '未填写姓名' }} · {{ detail.respondentEmail || '未填写邮箱' }}</p><div v-for="answer in detail.answers" :key="answer.questionId" class="answer-item"><strong>{{ answer.questionTitle || `题目 ${answer.questionId}` }}</strong><p>{{ answer.optionLabels?.join('、') || answer.content || '未回答' }}</p></div></div></div>
  </template>
</template>

<style scoped>
.ai-report-section + .ai-report-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e8edf4;
}

.ai-report-section h3 {
  margin: 0 0 14px;
  color: #253753;
  font-size: 15px;
}

.ai-finding {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.ai-finding-number {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 4px;
  color: #fff;
  background: #426b9f;
  font-size: 11px;
  font-weight: 700;
}

.ai-conclusion {
  margin: 1px 0 8px;
  color: #344662;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.65;
}

.ai-evidence-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.ai-evidence-list li {
  margin-top: 6px;
  color: #687891;
  font-size: 12px;
  line-height: 1.65;
}

.ai-evidence-list span {
  display: inline-block;
  margin-right: 7px;
  padding: 2px 5px;
  border-radius: 3px;
  color: #2d6848;
  background: #e7f5ec;
  font-size: 10px;
  font-weight: 700;
}

.ai-suggestions ol {
  margin: 0;
  padding-left: 20px;
  color: #53637c;
}

.ai-suggestions li {
  margin-bottom: 8px;
  padding-left: 3px;
  font-size: 13px;
  line-height: 1.7;
}

.ai-report-empty {
  margin: 0;
  color: #8190a7;
  font-size: 12px;
}

.ai-header-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.ai-new-chat-button {
  font-size: 12px;
}

.ai-chat-panel {
  border-top: 1px solid #e8edf4;
  background: #fbfcfe;
}

.ai-chat-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 24px 12px;
}

.ai-chat-heading h3 {
  margin: 0 0 3px;
  color: #253753;
  font-size: 14px;
}

.ai-chat-heading span,
.ai-chat-count {
  color: #8190a7;
  font-size: 10px;
}

.ai-chat-messages {
  display: grid;
  gap: 12px;
  max-height: 330px;
  padding: 6px 24px 16px;
  overflow-y: auto;
}

.ai-chat-message {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 9px;
  align-items: start;
}

.ai-chat-message > span {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 4px;
  color: #fff;
  background: #365f94;
  font-size: 10px;
  font-weight: 700;
}

.ai-chat-message.user > span {
  color: #52617e;
  background: #e7ecf3;
}

.ai-chat-message > div {
  padding: 9px 11px;
  border: 1px solid #e3e9f1;
  border-radius: 6px;
  background: #fff;
}

.ai-chat-message.user > div {
  background: #f2f6fb;
}

.ai-chat-message p {
  margin: 0;
  color: #465975;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.ai-chat-evidence {
  margin: 9px 0 0;
  padding: 9px 0 0 17px;
  border-top: 1px solid #edf0f5;
  color: #657791;
  font-size: 10px;
  line-height: 1.65;
}

.ai-chat-empty {
  margin: 0;
  padding: 4px 24px 14px;
  color: #8190a7;
  font-size: 12px;
}

.ai-chat-composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 9px;
  padding: 0 24px 20px;
}

.ai-chat-composer textarea {
  min-height: 62px;
  resize: none;
  font-size: 12px;
}

.ai-chat-send {
  width: 68px;
  color: #fff;
  border-color: #426b9f;
  background: #365f94;
}

.ai-chat-send:disabled {
  cursor: not-allowed;
  opacity: .55;
}

.review-card,
.feedback-card {
  width: 100%;
  max-width: none;
  margin-bottom: 18px;
  padding: 0;
  overflow: hidden;
}

.module-heading,
.review-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 20px 24px;
}

.module-heading {
  border-bottom: 1px solid #edf0f5;
}

.module-heading h2 {
  margin: 0 0 5px;
  color: #253753;
  font-size: 17px;
}

.module-heading p {
  margin: 0;
  color: #8190a7;
  font-size: 12px;
}

.module-count {
  flex: 0 0 auto;
  color: #ad5260;
  font-size: 12px;
  font-weight: 700;
}

.review-toolbar {
  padding-top: 14px;
  padding-bottom: 14px;
  background: #fafbfd;
}

.review-tabs {
  display: flex;
  gap: 4px;
}

.review-tabs button {
  border-color: transparent;
  background: transparent;
  font-size: 12px;
}

.review-tabs button.active {
  border-color: #cbd8e8;
  color: #315887;
  background: #edf4fc;
}

.review-list,
.feedback-list {
  padding: 0 24px;
}

.review-item {
  display: grid;
  grid-template-columns: 62px minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 18px 0;
  border-top: 1px solid #edf0f5;
}

.risk-score {
  display: grid;
  width: 56px;
  height: 56px;
  place-items: center;
  align-content: center;
  border: 1px solid #e2c777;
  border-radius: 6px;
  color: #765c16;
  background: #fff9e8;
}

.risk-score.high {
  border-color: #e5a9b1;
  color: #9b3444;
  background: #fff1f3;
}

.risk-score strong {
  font-size: 18px;
  line-height: 1;
}

.risk-score span {
  margin-top: 4px;
  font-size: 9px;
}

.review-title {
  display: flex;
  align-items: center;
  gap: 9px;
}

.review-title strong {
  color: #344662;
  font-size: 13px;
}

.review-status {
  padding: 3px 6px;
  border-radius: 3px;
  color: #765c16;
  background: #fff4d5;
  font-size: 10px;
}

.review-status.confirmed {
  color: #9b3444;
  background: #fff0f2;
}

.review-status.dismissed {
  color: #2d6848;
  background: #e7f5ec;
}

.review-content p {
  margin: 6px 0 9px;
  color: #8190a7;
  font-size: 11px;
}

.risk-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.risk-reasons span {
  padding: 3px 6px;
  border-radius: 3px;
  color: #667790;
  background: #f0f3f7;
  font-size: 10px;
}

.review-actions {
  display: flex;
  gap: 7px;
}

.module-error,
.module-empty {
  margin: 0;
  padding: 20px 24px;
  color: #8190a7;
  font-size: 12px;
}

.module-error {
  color: #b64755;
  background: #fff7f8;
}

.feedback-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-bottom: 1px solid #edf0f5;
  background: #fafbfd;
}

.feedback-summary div {
  padding: 18px 24px;
  border-right: 1px solid #edf0f5;
}

.feedback-summary div:last-child {
  border-right: 0;
}

.feedback-summary strong,
.feedback-summary span {
  display: block;
}

.feedback-summary strong {
  color: #304d77;
  font-size: 22px;
}

.feedback-summary span {
  margin-top: 4px;
  color: #8190a7;
  font-size: 10px;
}

.feedback-item {
  padding: 16px 0;
  border-top: 1px solid #edf0f5;
}

.feedback-rating {
  color: #d39b27;
  font-size: 13px;
  letter-spacing: 0;
}

.feedback-rating span {
  color: #d9dfe8;
}

.feedback-item p {
  margin: 8px 0;
  color: #465975;
  font-size: 13px;
  line-height: 1.65;
}

.feedback-item small {
  color: #8a98ab;
  font-size: 10px;
}

@media (max-width: 720px) {
  .ai-header-actions,
  .ai-chat-composer {
    grid-template-columns: 1fr;
    width: 100%;
  }

  .ai-header-actions {
    display: grid;
  }

  .ai-chat-heading,
  .ai-chat-messages,
  .ai-chat-empty,
  .ai-chat-composer {
    padding-right: 17px;
    padding-left: 17px;
  }

  .ai-chat-send {
    width: 100%;
  }

  .module-heading,
  .review-toolbar {
    align-items: stretch;
    flex-direction: column;
    padding: 17px;
  }

  .review-tabs {
    overflow-x: auto;
  }

  .review-tabs button {
    flex: 0 0 auto;
  }

  .review-list,
  .feedback-list {
    padding: 0 17px;
  }

  .review-item {
    grid-template-columns: 56px minmax(0, 1fr);
  }

  .review-actions {
    grid-column: 1 / -1;
  }

  .feedback-summary div {
    padding: 15px 12px;
  }
}
</style>
