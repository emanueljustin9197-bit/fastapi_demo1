<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { apiFetch, assetUrl } from '../api/client'
import { publicApi, type ResponseSource } from '../api/public'
import type { Questionnaire, QuestionItem } from '../types'

const props = defineProps<{ publicCode: string }>()
const survey = ref<Questionnaire | null>(null)
const answers = ref<Record<number, { optionIds: number[]; content: string | number }>>({})
const respondentName = ref('')
const respondentEmail = ref('')
const submitted = ref(false)
const showResultAfterSubmit = ref(false)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const startedAt = Date.now()
const sessionToken = ref('')
const submittedResponseId = ref<number | null>(null)
const feedbackRating = ref(0)
const feedbackIssueType = ref('none')
const feedbackContent = ref('')
const feedbackSubmitting = ref(false)
const feedbackSubmitted = ref(false)
const feedbackError = ref('')
let activityTimer: number | undefined

function detectResponseSource(): ResponseSource {
  const explicitSource = new URLSearchParams(window.location.search).get('source')
  if (explicitSource === 'qrCode' || explicitSource === 'wechat' || explicitSource === 'publicLink') {
    return explicitSource
  }
  return /MicroMessenger/i.test(navigator.userAgent) ? 'wechat' : 'publicLink'
}

const responseSource = detectResponseSource()

const sessionStorageKey = computed(() => `survey_session_${props.publicCode}`)
const backgroundUrl = computed(() => assetUrl(survey.value?.backgroundImage))
const publicPageStyle = computed((): Record<string, string> => {
  if (!backgroundUrl.value) return {}
  return {
    '--survey-background-image': `url(${JSON.stringify(backgroundUrl.value)})`,
  }
})

const requiresIdentity = computed(() => survey.value?.anonymous === false)

function answerOf(question: QuestionItem) {
  const id = question.id || 0
  return answers.value[id] || { optionIds: [], content: '' }
}

function selected(question: QuestionItem, optionId: number | undefined) {
  return optionId !== undefined && answerOf(question).optionIds.includes(optionId)
}

function submittedAnswerText(question: QuestionItem) {
  const answer = answerOf(question)
  if (question.type === 'single' || question.type === 'multiple') {
    const labels = question.options
      .filter((option) => option.id !== undefined && answer.optionIds.includes(option.id))
      .map((option) => option.label)
    return labels.join('、') || '未填写'
  }
  const content = String(answer.content ?? '').trim()
  if (!content) return '未填写'
  return question.type === 'rating' ? `${content} 分` : content
}

function toggle(question: QuestionItem, optionId: number) {
  const id = question.id || 0
  const answer = answerOf(question)
  if (question.type === 'single') {
    answer.optionIds = [optionId]
  } else {
    answer.optionIds = answer.optionIds.includes(optionId)
      ? answer.optionIds.filter((value) => value !== optionId)
      : [...answer.optionIds, optionId]
  }
  answers.value[id] = answer
  recordActivity()
}

async function startResponseSession() {
  const existingToken = sessionStorage.getItem(sessionStorageKey.value)
  if (existingToken) {
    sessionToken.value = existingToken
    return
  }

  try {
    const result = await apiFetch<{ sessionToken: string }>('/api/public/response/start', {
      method: 'POST',
      body: JSON.stringify({ publicCode: props.publicCode }),
    })
    sessionToken.value = result.sessionToken
    sessionStorage.setItem(sessionStorageKey.value, result.sessionToken)
  } catch {
    // Keep submissions compatible while the session API is being deployed.
  }
}

function recordActivity() {
  if (!sessionToken.value || submitted.value) return
  window.clearTimeout(activityTimer)
  activityTimer = window.setTimeout(async () => {
    try {
      await apiFetch('/api/public/response/activity', {
        method: 'POST',
        body: JSON.stringify({ sessionToken: sessionToken.value }),
      })
    } catch {
      // Activity tracking must never prevent someone from completing a survey.
    }
  }, 800)
}

function isAnswered(question: QuestionItem) {
  const answer = answerOf(question)
  return answer.optionIds.length > 0 || Boolean(String(answer.content ?? '').trim())
}

function validate() {
  if (!survey.value) return false
  if (requiresIdentity.value) {
    if (!respondentName.value.trim()) {
      error.value = '请输入姓名'
      return false
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(respondentEmail.value.trim())) {
      error.value = '请输入正确的邮箱地址'
      return false
    }
  }
  const requiredQuestion = survey.value.questions.find((question) =>
    question.required && !isAnswered(question),
  )
  if (requiredQuestion) {
    error.value = `请完成必填题：${requiredQuestion.title}`
    return false
  }
  return true
}

async function submit() {
  error.value = ''
  if (!validate() || !survey.value) return
  submitting.value = true
  try {
    const payload = {
      publicCode: props.publicCode,
      sessionToken: sessionToken.value || undefined,
      source: responseSource,
      durationSeconds: Math.max(0, Math.round((Date.now() - startedAt) / 1000)),
      respondentName: requiresIdentity.value ? respondentName.value.trim() : null,
      respondentEmail: requiresIdentity.value ? respondentEmail.value.trim() : null,
      answers: survey.value.questions
        .filter((question) => question.id !== undefined && isAnswered(question))
        .map((question) => ({
          questionId: question.id as number,
          optionIds: answerOf(question).optionIds,
          content: String(answerOf(question).content ?? '').trim() || null,
        })),
    }
    const result = await publicApi.submitResponse(payload) as unknown as {
      id?: number
      responseId?: number
      showResult?: boolean
    }
    submittedResponseId.value = result.responseId || result.id || null
    showResultAfterSubmit.value = Boolean(result.showResult)
    sessionStorage.removeItem(sessionStorageKey.value)
    submitted.value = true
  } catch (submitError) {
    error.value = (submitError as Error).message
  } finally {
    submitting.value = false
  }
}

async function submitFeedback() {
  if (!feedbackRating.value) {
    feedbackError.value = '请选择 1 到 5 分'
    return
  }
  feedbackSubmitting.value = true
  feedbackError.value = ''
  try {
    await apiFetch('/api/public/feedback', {
      method: 'POST',
      body: JSON.stringify({
        publicCode: props.publicCode,
        questionnaireId: survey.value?.id,
        responseId: submittedResponseId.value,
        rating: feedbackRating.value,
        issueType: feedbackIssueType.value,
        content: feedbackContent.value.trim() || null,
      }),
    })
    feedbackSubmitted.value = true
  } catch (submitError) {
    feedbackError.value = (submitError as Error).message
  } finally {
    feedbackSubmitting.value = false
  }
}

onMounted(async () => {
  try {
    survey.value = await publicApi.questionnaire(props.publicCode)
    survey.value.questions.forEach((question) => {
      if (question.id !== undefined) {
        answers.value[question.id] = { optionIds: [], content: '' }
      }
    })
    await startResponseSession()
  } catch (loadError) {
    error.value = (loadError as Error).message
  } finally {
    loading.value = false
  }
})

onUnmounted(() => window.clearTimeout(activityTimer))
</script>

<template>
  <div class="public-page" :class="{ 'has-background': backgroundUrl }" :style="publicPageStyle">
    <div v-if="loading" class="card empty">正在加载...</div>
    <div v-else-if="error && !survey" class="card error">{{ error }}</div>
    <div v-else-if="submitted" class="card success-page submission-success">
      <div class="success-heading">
        <span class="success-mark">✓</span>
        <div><h1>提交成功</h1><p>感谢你的参与。</p></div>
      </div>
      <section v-if="showResultAfterSubmit && survey" class="submitted-result">
        <div class="submitted-result-head"><h2>本次答卷</h2><span>{{ survey.questions.length }} 道题</span></div>
        <div v-for="(question, index) in survey.questions" :key="question.id || index" class="submitted-result-row">
          <span>{{ index + 1 }}. {{ question.title }}</span>
          <strong>{{ submittedAnswerText(question) }}</strong>
        </div>
      </section>
      <div v-if="feedbackSubmitted" class="feedback-thanks">
        <strong>反馈已提交</strong>
        <p>感谢你帮助我们改善填写体验。</p>
      </div>
      <section v-else class="feedback-form">
        <div class="feedback-form-heading">
          <h2>这次填写体验怎么样？</h2>
          <span>选填，不影响已经提交的答卷</span>
        </div>
        <div class="rating-control" role="radiogroup" aria-label="填写体验评分">
          <button
            v-for="score in 5"
            :key="score"
            type="button"
            :class="{ selected: feedbackRating >= score }"
            :aria-label="`${score} 分`"
            :aria-checked="feedbackRating === score"
            role="radio"
            @click="feedbackRating = score"
          >★</button>
          <span>{{ feedbackRating ? `${feedbackRating} 分` : '请选择评分' }}</span>
        </div>
        <label class="feedback-field">
          <span>是否遇到问题</span>
          <select v-model="feedbackIssueType">
            <option value="none">没有遇到问题</option>
            <option value="usability">操作不方便</option>
            <option value="content">题目或内容有问题</option>
            <option value="performance">加载或提交较慢</option>
            <option value="other">其他问题</option>
          </select>
        </label>
        <label class="feedback-field">
          <span>补充说明</span>
          <textarea v-model="feedbackContent" maxlength="500" placeholder="可以告诉我们哪里需要改进" />
        </label>
        <div v-if="feedbackError" class="feedback-error">{{ feedbackError }}</div>
        <button class="primary feedback-submit" type="button" :disabled="feedbackSubmitting" @click="submitFeedback">
          {{ feedbackSubmitting ? '正在提交...' : '提交体验反馈' }}
        </button>
      </section>
    </div>
    <div v-else-if="survey" class="public-card" @input="recordActivity">
      <h1>{{ survey.title }}</h1>
      <p>{{ survey.description }}</p>

      <div v-if="requiresIdentity" class="identity-fields">
        <h2>填写者信息</h2>
        <label>
          姓名
          <input v-model="respondentName" autocomplete="name" placeholder="请输入姓名" />
        </label>
        <label>
          邮箱
          <input v-model="respondentEmail" type="email" autocomplete="email" placeholder="请输入邮箱" />
        </label>
      </div>

      <div v-for="(question, index) in survey.questions" :key="question.id" class="public-question">
        <h3>
          {{ index + 1 }}. {{ question.title }}
          <small v-if="question.required">* 必填</small>
        </h3>
        <div v-if="question.type === 'single' || question.type === 'multiple'">
          <button
            v-for="option in question.options"
            :key="option.id"
            class="choice"
            :class="{ selected: selected(question, option.id) }"
            @click="toggle(question, option.id || 0)"
          >
            {{ selected(question, option.id) ? '✓' : '○' }} {{ option.label }}
          </button>
        </div>
        <input
          v-else-if="question.type === 'date'"
          v-model="answers[question.id || 0].content"
          type="date"
        />
        <input
          v-else-if="question.type === 'rating'"
          v-model="answers[question.id || 0].content"
          type="number"
          min="1"
          max="5"
          placeholder="1 - 5"
        />
        <input
          v-else-if="question.type === 'number'"
          v-model="answers[question.id || 0].content"
          type="number"
          placeholder="请输入数字"
        />
        <input
          v-else-if="question.type === 'phone'"
          v-model="answers[question.id || 0].content"
          type="tel"
          placeholder="请输入电话号码"
        />
        <textarea
          v-else
          v-model="answers[question.id || 0].content"
          placeholder="请输入回答"
        />
      </div>

      <div v-if="error" class="error">{{ error }}</div>
      <button class="primary full" :disabled="submitting" @click="submit">
        {{ submitting ? '提交中...' : '提交答卷' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.submission-success {
  max-width: 680px;
  text-align: left;
}

.success-heading {
  display: flex;
  align-items: center;
  gap: 14px;
}

.success-heading h1,
.success-heading p,
.feedback-thanks p {
  margin: 0;
}

.success-heading p {
  margin-top: 4px;
  color: #718099;
}

.success-mark {
  display: grid;
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #2f8658;
  font-size: 22px;
}

.feedback-form,
.feedback-thanks,
.submitted-result {
  margin-top: 25px;
  padding-top: 22px;
  border-top: 1px solid #e4e9f0;
}

.submitted-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.submitted-result-head h2 {
  margin: 0;
  color: #2d405e;
  font-size: 17px;
}

.submitted-result-head span {
  color: #8b96a8;
  font-size: 11px;
}

.submitted-result-row {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 18px;
  padding: 12px 0;
  border-bottom: 1px solid #edf0f4;
}

.submitted-result-row > span {
  color: #738097;
  font-size: 12px;
  line-height: 1.6;
}

.submitted-result-row strong {
  overflow-wrap: anywhere;
  color: #34445f;
  font-size: 12px;
  line-height: 1.6;
  text-align: right;
}

.feedback-form-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.feedback-form-heading h2 {
  margin: 0;
  color: #2d405e;
  font-size: 17px;
}

.feedback-form-heading span {
  color: #8a97a9;
  font-size: 11px;
}

.rating-control {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 17px 0;
}

.rating-control button {
  width: 34px;
  height: 34px;
  padding: 0;
  border: 0;
  color: #d9dfe8;
  background: transparent;
  font-size: 25px;
}

.rating-control button.selected {
  color: #d39b27;
}

.rating-control span {
  margin-left: 8px;
  color: #718099;
  font-size: 12px;
}

.feedback-field {
  display: grid;
  gap: 7px;
  margin-top: 14px;
  color: #53637c;
  font-size: 12px;
}

.feedback-field textarea {
  min-height: 92px;
  resize: vertical;
}

.feedback-error {
  margin-top: 12px;
  color: #b64755;
  font-size: 12px;
}

.feedback-submit {
  margin-top: 16px;
}

.feedback-thanks strong {
  color: #2d6848;
}

.feedback-thanks p {
  margin-top: 6px;
  color: #718099;
  font-size: 13px;
}

@media (max-width: 620px) {
  .feedback-form-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .rating-control {
    flex-wrap: wrap;
  }

  .submitted-result-row {
    grid-template-columns: 1fr;
    gap: 5px;
  }

  .submitted-result-row strong {
    text-align: left;
  }
}
</style>
