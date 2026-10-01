<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { assetUrl, apiFetch } from '../api/client'
import { questionnaireApi } from '../api/questionnaire'
import type { Questionnaire, QuestionItem, QuestionType } from '../types'

type ShareInfo = {
  id?: number
  status?: string
  publicUrl?: string
  publicCode?: string
  qrCodeUrl?: string
  publishedAt?: string
}

type QuestionnaireForm = Questionnaire & {
  responseTimeoutMinutes: number
}

type SettingsSnapshot = {
  anonymous: boolean
  oneResponse: boolean
  showResult: boolean
  responseTimeoutMinutes: number
}

type TemplateCategory = 'recommended' | 'research' | 'collection' | 'feedback' | 'employee' | 'event'

type SurveyTemplate = {
  id: string
  category: Exclude<TemplateCategory, 'recommended'>
  featured: boolean
  title: string
  description: string
  label: string
  accent: string
  anonymous: boolean
  responseTimeoutMinutes: number
  questions: QuestionItem[]
}

function templateQuestion(
  type: QuestionType,
  title: string,
  required = true,
  optionLabels: string[] = [],
): QuestionItem {
  return {
    type,
    title,
    required,
    sortOrder: 0,
    options: optionLabels.map((label, index) => ({ label, sortOrder: index })),
  }
}

const templateCategories: Array<{ id: TemplateCategory; label: string }> = [
  { id: 'recommended', label: '推荐' },
  { id: 'research', label: '调研问卷' },
  { id: 'collection', label: '信息收集' },
  { id: 'feedback', label: '反馈收集' },
  { id: 'employee', label: '员工管理' },
  { id: 'event', label: '活动报名' },
]

const surveyTemplates: SurveyTemplate[] = [
  {
    id: 'employee-satisfaction',
    category: 'employee',
    featured: true,
    title: '员工满意度调研',
    description: '了解员工对工作环境、团队协作与成长空间的真实感受。',
    label: '员工',
    accent: '#5576d9',
    anonymous: true,
    responseTimeoutMinutes: 15,
    questions: [
      templateQuestion('single', '你在公司的工作年限是？', true, ['不足 1 年', '1-3 年', '3-5 年', '5 年以上']),
      templateQuestion('single', '你对当前工作内容的整体满意度如何？', true, ['非常满意', '满意', '一般', '不满意', '非常不满意']),
      templateQuestion('rating', '你愿意向朋友推荐本公司作为工作场所吗？'),
      templateQuestion('single', '你认为团队内部的沟通是否顺畅？', true, ['非常顺畅', '比较顺畅', '一般', '不太顺畅']),
      templateQuestion('multiple', '你最希望公司改善哪些方面？', true, ['薪酬福利', '晋升机制', '培训成长', '团队协作', '办公环境']),
      templateQuestion('text', '你对公司还有哪些建议？', false),
    ],
  },
  {
    id: 'customer-satisfaction',
    category: 'research',
    featured: true,
    title: '客户满意度调研',
    description: '收集客户对产品、服务过程和整体体验的评价。',
    label: '客户',
    accent: '#2f8f83',
    anonymous: true,
    responseTimeoutMinutes: 10,
    questions: [
      templateQuestion('single', '你使用我们的产品或服务多久了？', true, ['首次使用', '不足 3 个月', '3-12 个月', '1 年以上']),
      templateQuestion('rating', '请为本次整体体验评分'),
      templateQuestion('single', '产品是否满足了你的主要需求？', true, ['完全满足', '基本满足', '部分满足', '未满足']),
      templateQuestion('multiple', '你最看重哪些方面？', true, ['产品质量', '使用体验', '服务响应', '价格', '品牌信誉']),
      templateQuestion('single', '你是否愿意继续使用我们的产品？', true, ['愿意', '暂不确定', '不愿意']),
      templateQuestion('text', '最希望我们优先改进什么？', false),
    ],
  },
  {
    id: 'event-registration',
    category: 'event',
    featured: true,
    title: '活动报名表',
    description: '适用于分享会、沙龙、培训和线下活动的报名登记。',
    label: '活动',
    accent: '#b46f3f',
    anonymous: false,
    responseTimeoutMinutes: 10,
    questions: [
      templateQuestion('text', '姓名'),
      templateQuestion('phone', '联系电话'),
      templateQuestion('text', '所在公司或组织', false),
      templateQuestion('single', '你希望参加哪个场次？', true, ['上午场', '下午场', '晚间场']),
      templateQuestion('multiple', '你关注哪些主题？', false, ['行业趋势', '实战案例', '产品体验', '交流合作']),
      templateQuestion('text', '其他备注', false),
    ],
  },
  {
    id: 'product-feedback',
    category: 'feedback',
    featured: true,
    title: '产品体验反馈',
    description: '快速定位使用障碍、功能需求和产品体验问题。',
    label: '反馈',
    accent: '#8a62bd',
    anonymous: true,
    responseTimeoutMinutes: 12,
    questions: [
      templateQuestion('single', '你使用产品的频率是？', true, ['每天', '每周数次', '偶尔', '首次使用']),
      templateQuestion('rating', '请为产品的易用性评分'),
      templateQuestion('multiple', '你经常使用哪些功能？', true, ['内容创建', '数据管理', '协作分享', '统计分析', '其他']),
      templateQuestion('single', '使用过程中是否遇到问题？', true, ['没有', '偶尔遇到', '经常遇到']),
      templateQuestion('text', '请描述你遇到的问题或建议', false),
      templateQuestion('single', '是否愿意参与后续访谈？', false, ['愿意', '暂不考虑']),
    ],
  },
  {
    id: 'meeting-checkin',
    category: 'collection',
    featured: true,
    title: '会议签到表',
    description: '登记参会人员信息、到场时间与所属部门。',
    label: '签到',
    accent: '#3d7eae',
    anonymous: false,
    responseTimeoutMinutes: 5,
    questions: [
      templateQuestion('text', '姓名'),
      templateQuestion('text', '部门或单位'),
      templateQuestion('phone', '联系电话'),
      templateQuestion('single', '参会方式', true, ['现场参会', '线上参会']),
    ],
  },
  {
    id: 'training-feedback',
    category: 'feedback',
    featured: false,
    title: '培训效果反馈',
    description: '评估课程内容、讲师表现及培训后的实际收获。',
    label: '培训',
    accent: '#287f67',
    anonymous: true,
    responseTimeoutMinutes: 10,
    questions: [
      templateQuestion('rating', '请为本次培训的整体效果评分'),
      templateQuestion('single', '课程内容与你的工作相关度如何？', true, ['非常相关', '比较相关', '一般', '不相关']),
      templateQuestion('rating', '请为讲师的表达与互动评分'),
      templateQuestion('multiple', '本次培训带给你哪些收获？', true, ['知识拓展', '技能提升', '问题解决思路', '团队交流']),
      templateQuestion('text', '你认为课程最有价值的部分是什么？', false),
      templateQuestion('text', '你希望后续增加哪些内容？', false),
    ],
  },
  {
    id: 'candidate-information',
    category: 'employee',
    featured: false,
    title: '候选人信息登记',
    description: '统一收集求职者的基本信息、工作经验和到岗意向。',
    label: '招聘',
    accent: '#536b9f',
    anonymous: false,
    responseTimeoutMinutes: 20,
    questions: [
      templateQuestion('text', '姓名'),
      templateQuestion('phone', '联系电话'),
      templateQuestion('text', '应聘岗位'),
      templateQuestion('number', '相关工作年限'),
      templateQuestion('single', '最高学历', true, ['高中及以下', '大专', '本科', '硕士及以上']),
      templateQuestion('date', '预计到岗日期', false),
      templateQuestion('text', '个人优势或补充说明', false),
    ],
  },
  {
    id: 'market-research',
    category: 'research',
    featured: false,
    title: '市场需求调研',
    description: '验证目标人群、使用场景、购买因素与价格预期。',
    label: '市场',
    accent: '#a55d72',
    anonymous: true,
    responseTimeoutMinutes: 12,
    questions: [
      templateQuestion('single', '你对这类产品的了解程度是？', true, ['非常了解', '有所了解', '听说过', '完全不了解']),
      templateQuestion('single', '你目前是否正在使用同类产品？', true, ['正在使用', '曾经使用', '从未使用']),
      templateQuestion('multiple', '你通常在哪些场景下使用？', true, ['工作', '学习', '生活管理', '娱乐', '其他']),
      templateQuestion('multiple', '哪些因素最影响你的选择？', true, ['功能', '易用性', '价格', '口碑', '售后服务']),
      templateQuestion('single', '你可接受的价格区间是？', true, ['免费', '50 元以内', '50-200 元', '200 元以上']),
      templateQuestion('text', '你最期待解决的问题是什么？', false),
    ],
  },
]

const props = defineProps<{ token: string; questionnaireId: number | null }>()
const emit = defineEmits<{ saved: [] }>()
const saving = ref(false)
const collectionUpdating = ref(false)
const aiLoading = ref(false)
const aiPrompt = ref('')
const loadError = ref('')
const shareInfo = ref<ShareInfo | null>(null)
const publishSuccess = ref(false)
const copied = ref(false)
const backgroundFile = ref<File | null>(null)
const backgroundPreviewObjectUrl = ref('')
const backgroundUploading = ref(false)
const previewOpen = ref(false)
const settingsOpen = ref(false)
const previewViewport = ref<'desktop' | 'mobile'>('desktop')
const templateGalleryOpen = ref(!props.questionnaireId)
const templateCategory = ref<TemplateCategory>('recommended')
const templateSearch = ref('')
const selectedTemplateName = ref('')
let previousBodyOverflow = ''
let settingsSnapshot: SettingsSnapshot | null = null
const form = ref<QuestionnaireForm>({
  title: '',
  description: '',
  anonymous: true,
  oneResponse: false,
  showResult: false,
  responseTimeoutMinutes: 30,
  questions: [],
})

const isPublished = computed(() => form.value.status === 'active')
const filteredTemplates = computed(() => {
  const keyword = templateSearch.value.trim().toLowerCase()
  return surveyTemplates.filter((template) => {
    const inCategory = templateCategory.value === 'recommended'
      ? template.featured
      : template.category === templateCategory.value
    const matchesKeyword = !keyword || `${template.title}${template.description}${template.label}`.toLowerCase().includes(keyword)
    return inCategory && matchesKeyword
  })
})
const requiredQuestionCount = computed(() => form.value.questions.filter((question) => question.required).length)
const hasDraftContent = computed(() => Boolean(
  form.value.title.trim() || form.value.description?.trim() || form.value.questions.length,
))
const backgroundPreviewUrl = computed(() => (
  backgroundPreviewObjectUrl.value || assetUrl(form.value.backgroundImage)
))
const backgroundPreviewStyle = computed((): Record<string, string> => {
  if (!backgroundPreviewUrl.value) return {}
  return {
    backgroundImage: `linear-gradient(rgba(20, 29, 48, .18), rgba(20, 29, 48, .18)), url(${JSON.stringify(backgroundPreviewUrl.value)})`,
  }
})
const previewPageStyle = computed((): Record<string, string> => {
  if (!backgroundPreviewUrl.value) return {}
  return {
    '--editor-preview-background': `url(${JSON.stringify(backgroundPreviewUrl.value)})`,
  }
})
const shareCode = computed(() => shareInfo.value?.publicCode || form.value.publicCode || '')
const shareUrl = computed(() => {
  const savedUrl = shareInfo.value?.publicUrl || form.value.publicUrl
  if (savedUrl) return savedUrl
  return shareCode.value ? `${window.location.origin}/s/${shareCode.value}` : ''
})
const qrCodeUrl = computed(() => {
  const path = shareInfo.value?.qrCodeUrl || (shareCode.value
    ? `/api/questionnaire/qrcode?publicCode=${encodeURIComponent(shareCode.value)}`
    : '')
  return assetUrl(path)
})

const types: Array<[QuestionType, string]> = [
  ['single', '单选题'],
  ['multiple', '多选题'],
  ['text', '问答题'],
  ['date', '日期题'],
  ['rating', '评分题'],
  ['number', '数字题'],
  ['phone', '电话题'],
]

function addQuestion(type: QuestionType = 'single') {
  form.value.questions.push({
    type,
    title: '',
    required: true,
    sortOrder: form.value.questions.length,
    options: type === 'single' || type === 'multiple'
      ? [{ label: '选项 1', sortOrder: 0 }, { label: '选项 2', sortOrder: 1 }]
      : [],
  })
}

function resetNewForm() {
  clearBackgroundObjectUrl()
  backgroundFile.value = null
  shareInfo.value = null
  publishSuccess.value = false
  form.value = {
    title: '',
    description: '',
    anonymous: true,
    oneResponse: false,
    showResult: false,
    responseTimeoutMinutes: 30,
    questions: [],
  }
}

function confirmTemplateReplacement() {
  return !hasDraftContent.value || window.confirm('使用新的模板会替换当前未保存的内容，是否继续？')
}

function startBlank() {
  if (!confirmTemplateReplacement()) return
  resetNewForm()
  selectedTemplateName.value = ''
  addQuestion()
  templateGalleryOpen.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function useTemplate(template: SurveyTemplate) {
  if (!confirmTemplateReplacement()) return
  resetNewForm()
  form.value.title = template.title
  form.value.description = template.description
  form.value.anonymous = template.anonymous
  form.value.oneResponse = false
  form.value.showResult = false
  form.value.responseTimeoutMinutes = template.responseTimeoutMinutes
  form.value.questions = template.questions.map((question, index) => ({
    ...question,
    sortOrder: index,
    options: question.options.map((option, optionIndex) => ({
      ...option,
      sortOrder: optionIndex,
    })),
  }))
  selectedTemplateName.value = template.title
  templateGalleryOpen.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function openTemplateGallery() {
  templateGalleryOpen.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function closeTemplateGallery() {
  templateGalleryOpen.value = false
}

function normalize() {
  form.value.questions.forEach((question, index) => {
    question.sortOrder = index
    question.options = ['single', 'multiple'].includes(question.type)
      ? question.options.map((option, optionIndex) => ({ ...option, sortOrder: optionIndex }))
      : []
  })
}

function questionnairePayload() {
  return {
    title: form.value.title.trim(),
    description: form.value.description?.trim() || null,
    anonymous: Boolean(form.value.anonymous),
    oneResponse: Boolean(form.value.oneResponse),
    showResult: Boolean(form.value.showResult),
    responseTimeoutMinutes: form.value.responseTimeoutMinutes,
    questions: form.value.questions.map((question, index) => ({
      id: question.id,
      type: question.type,
      title: question.title.trim(),
      required: Boolean(question.required),
      sortOrder: index,
      options: ['single', 'multiple'].includes(question.type)
        ? question.options.map((option, optionIndex) => ({
            id: option.id,
            label: option.label.trim(),
            sortOrder: optionIndex,
          }))
        : [],
    })),
  }
}

function clearBackgroundObjectUrl() {
  if (backgroundPreviewObjectUrl.value) {
    URL.revokeObjectURL(backgroundPreviewObjectUrl.value)
    backgroundPreviewObjectUrl.value = ''
  }
}

async function uploadPendingBackground() {
  if (!form.value.id || !backgroundFile.value) return
  backgroundUploading.value = true
  try {
    const result = await questionnaireApi.uploadBackground(
      form.value.id,
      backgroundFile.value,
      props.token,
    )
    form.value.backgroundImage = result.backgroundImage
    backgroundFile.value = null
    clearBackgroundObjectUrl()
  } finally {
    backgroundUploading.value = false
  }
}

async function selectBackground(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    alert('仅支持 JPG、PNG 或 WEBP 图片')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('背景图片不能超过 5MB')
    return
  }

  clearBackgroundObjectUrl()
  backgroundFile.value = file
  backgroundPreviewObjectUrl.value = URL.createObjectURL(file)

  if (form.value.id) {
    try {
      await uploadPendingBackground()
    } catch (error) {
      backgroundFile.value = null
      clearBackgroundObjectUrl()
      alert((error as Error).message)
    }
  }
}

async function removeBackground() {
  if (!backgroundPreviewUrl.value || backgroundUploading.value) return
  backgroundFile.value = null
  clearBackgroundObjectUrl()

  if (!form.value.id) {
    form.value.backgroundImage = null
    return
  }

  backgroundUploading.value = true
  try {
    await questionnaireApi.removeBackground(form.value.id, props.token)
    form.value.backgroundImage = null
  } catch (error) {
    alert((error as Error).message)
  } finally {
    backgroundUploading.value = false
  }
}

async function save(publish = false, navigateAfterSave = true): Promise<boolean> {
  normalize()
  if (!form.value.title.trim()) {
    alert('请输入表格名称')
    return false
  }
  if (!Number.isInteger(form.value.responseTimeoutMinutes) ||
      form.value.responseTimeoutMinutes < 1 ||
      form.value.responseTimeoutMinutes > 1440) {
    alert('最长填写时间必须是 1 到 1440 分钟之间的整数')
    return false
  }
  if (!form.value.questions.length) {
    alert('请至少添加一道题目')
    return false
  }
  if (form.value.questions.some((question) => !question.title.trim())) {
    alert('请填写所有题目标题')
    return false
  }
  if (form.value.questions.some((question) =>
    ['single', 'multiple'].includes(question.type) &&
    (!question.options.length || question.options.some((option) => !option.label.trim()))
  )) {
    alert('选择题至少需要一个有效选项')
    return false
  }

  saving.value = true
  try {
    if (form.value.id) {
      await apiFetch('/api/questionnaire/update', {
        method: 'PUT',
        body: JSON.stringify({ id: form.value.id, ...questionnairePayload() }),
      }, props.token)
    } else {
      const created = await apiFetch<{ id: number }>('/api/questionnaire/create', {
        method: 'POST',
        body: JSON.stringify(questionnairePayload()),
      }, props.token)
      form.value.id = created.id
    }
    await uploadPendingBackground()
    if (publish && form.value.id) {
      shareInfo.value = await questionnaireApi.publish(form.value.id, props.token)
      form.value.status = 'active'
      form.value.publicCode = shareInfo.value.publicCode || null
      form.value.publicUrl = shareInfo.value.publicUrl || null
      form.value.publishedAt = shareInfo.value.publishedAt || null
      publishSuccess.value = true
      return true
    }
    if (navigateAfterSave) emit('saved')
    return true
  } catch (error) {
    alert((error as Error).message)
    return false
  } finally {
    saving.value = false
  }
}

async function toggleCollection(event: Event) {
  const input = event.target as HTMLInputElement
  const shouldCollect = input.checked
  if (!form.value.id) {
    input.checked = false
    alert('请先保存问卷，再开启收集')
    return
  }

  collectionUpdating.value = true
  try {
    if (shouldCollect) {
      const result = await questionnaireApi.publish(form.value.id, props.token)
      shareInfo.value = result
      form.value.status = 'active'
      form.value.publicCode = result.publicCode || null
      form.value.publicUrl = result.publicUrl || null
      form.value.publishedAt = result.publishedAt || null
    } else {
      await questionnaireApi.close(form.value.id, props.token)
      form.value.status = 'closed'
      publishSuccess.value = false
    }
  } catch (error) {
    input.checked = isPublished.value
    alert((error as Error).message)
  } finally {
    collectionUpdating.value = false
  }
}

async function generateWithAi() {
  if (!aiPrompt.value.trim()) return alert('请先输入生成要求')
  aiLoading.value = true
  try {
    const result = await apiFetch<{
      title?: string
      description?: string
      questions: QuestionItem[]
    }>('/api/ai/questionnaire/generate', {
      method: 'POST',
      body: JSON.stringify({
        prompt: aiPrompt.value,
        questionCount: 8,
        title: form.value.title || undefined,
        existingQuestions: form.value.questions,
      }),
    }, props.token)
    if (result.title && !form.value.title) form.value.title = result.title
    if (result.description && !form.value.description) form.value.description = result.description
    form.value.questions = result.questions.map((question, index) => ({
      ...question,
      sortOrder: index,
      options: ['single', 'multiple'].includes(question.type) ? question.options || [] : [],
    }))
  } catch (error) {
    alert((error as Error).message)
  } finally {
    aiLoading.value = false
  }
}

async function copyPublicUrl() {
  if (!shareUrl.value) return alert('分享链接暂未加载，请刷新页面后重试。')
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
    window.setTimeout(() => { copied.value = false }, 1600)
  } catch {
    alert(shareUrl.value)
  }
}

function selectShareUrl(event: FocusEvent) {
  ;(event.target as HTMLInputElement).select()
}

function lockBodyScroll() {
  if (!previewOpen.value && !settingsOpen.value) {
    previousBodyOverflow = document.body.style.overflow
  }
  document.body.style.overflow = 'hidden'
}

function releaseBodyScroll() {
  if (!previewOpen.value && !settingsOpen.value) {
    document.body.style.overflow = previousBodyOverflow
  }
}

function openSettings() {
  settingsSnapshot = {
    anonymous: form.value.anonymous,
    oneResponse: Boolean(form.value.oneResponse),
    showResult: Boolean(form.value.showResult),
    responseTimeoutMinutes: form.value.responseTimeoutMinutes,
  }
  lockBodyScroll()
  settingsOpen.value = true
}

function closeSettings(restore = true) {
  if (saving.value) return
  if (restore && settingsSnapshot) {
    form.value.anonymous = settingsSnapshot.anonymous
    form.value.oneResponse = settingsSnapshot.oneResponse
    form.value.showResult = settingsSnapshot.showResult
    form.value.responseTimeoutMinutes = settingsSnapshot.responseTimeoutMinutes
  }
  settingsSnapshot = null
  settingsOpen.value = false
  releaseBodyScroll()
}

async function saveSettings() {
  const saved = await save(false, false)
  if (saved) closeSettings(false)
}

function openPreview() {
  lockBodyScroll()
  previewOpen.value = true
}

function closePreview() {
  previewOpen.value = false
  releaseBodyScroll()
}

function handleOverlayKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (previewOpen.value) closePreview()
  else if (settingsOpen.value) closeSettings()
}

onMounted(async () => {
  window.addEventListener('keydown', handleOverlayKeydown)
  try {
    if (props.questionnaireId) {
      const detail = await questionnaireApi.detail(props.questionnaireId, props.token)
      const savedTimeout = Number((detail as QuestionnaireForm).responseTimeoutMinutes)
      form.value = {
        ...detail,
        responseTimeoutMinutes: Number.isInteger(savedTimeout) && savedTimeout > 0
          ? savedTimeout
          : 30,
      }
      if (form.value.status === 'active') {
        // Older detail responses may omit public fields; the list response still has them.
        if (!form.value.publicUrl || !form.value.publicCode) {
          try {
            const result = await questionnaireApi.list({ page: 1, pageSize: 100 }, props.token)
            const item = result.list.find((item) => item.id === form.value.id)

            if (item) {
              form.value.publicCode = item.publicCode || null
              form.value.publicUrl = item.publicUrl || null
              form.value.publishedAt = item.publishedAt || null
            }
          } catch {
            // Keep the editor usable even when the share metadata fallback fails.
          }
        }

        shareInfo.value = {
          id: form.value.id,
          status: form.value.status,
          publicCode: form.value.publicCode || undefined,
          publicUrl: form.value.publicUrl || undefined,
          publishedAt: form.value.publishedAt || undefined,
        }
      }
    }
  } catch (error) {
    loadError.value = (error as Error).message
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleOverlayKeydown)
  if (previewOpen.value || settingsOpen.value) document.body.style.overflow = previousBodyOverflow
  clearBackgroundObjectUrl()
})
</script>

<template>
  <header class="page-header" :class="{ 'template-page-header': templateGalleryOpen }">
    <div>
      <h1>{{ templateGalleryOpen ? '选择问卷模板' : form.id ? '编辑表格' : '创建表格' }}</h1>
      <p>{{ templateGalleryOpen ? '从成熟结构开始，快速生成一份可自由编辑的问卷' : '设计、发布并分享你的在线表格' }}</p>
    </div>
    <div v-if="templateGalleryOpen && hasDraftContent" class="header-actions">
      <button type="button" @click="closeTemplateGallery">返回当前编辑</button>
    </div>
    <div v-else-if="!templateGalleryOpen" class="header-actions">
      <button v-if="!form.id && !isPublished" type="button" @click="openTemplateGallery">更换模板</button>
      <button type="button" @click="openSettings">表格设置</button>
      <button type="button" @click="openPreview">预览</button>
      <button :disabled="saving" @click="save(false)">{{ isPublished ? '保存修改' : '保存草稿' }}</button>
      <button class="primary" :disabled="saving" @click="isPublished ? copyPublicUrl() : save(true)">{{ isPublished ? (copied ? '链接已复制' : '复制分享链接') : saving ? '保存中...' : '发布表格' }}</button>
    </div>
  </header>

  <div v-if="loadError" class="card error">{{ loadError }}</div>
  <div v-if="publishSuccess && shareInfo" class="publish-success"><strong>发布成功</strong><span>公开链接已生成，可立即分享给填写者。</span><button @click="copyPublicUrl">{{ copied ? '链接已复制' : '复制链接' }}</button><button class="primary" @click="emit('saved')">返回我的表格</button></div>

  <section v-if="templateGalleryOpen" class="template-library">
    <div class="template-start-band">
      <div class="template-start-copy">
        <span class="template-eyebrow">QUICK START</span>
        <h2>从一个清晰的结构开始</h2>
        <p>选择模板后，标题、问题和选项会立即进入编辑器。</p>
      </div>
      <button class="blank-template-button" type="button" @click="startBlank">
        <span class="blank-template-icon">＋</span>
        <span><strong>新建空白问卷</strong><small>从第一道题开始设计</small></span>
      </button>
    </div>

    <div class="template-browser">
      <aside class="template-categories" aria-label="模板分类">
        <strong>模板分类</strong>
        <button
          v-for="category in templateCategories"
          :key="category.id"
          type="button"
          :class="{ active: templateCategory === category.id }"
          @click="templateCategory = category.id"
        >
          {{ category.label }}
        </button>
      </aside>

      <div class="template-results">
        <div class="template-results-head">
          <div>
            <h2>{{ templateCategories.find((category) => category.id === templateCategory)?.label }}</h2>
            <span>{{ filteredTemplates.length }} 个模板</span>
          </div>
          <label class="template-search">
            <span aria-hidden="true">⌕</span>
            <input v-model="templateSearch" type="search" placeholder="搜索模板" />
          </label>
        </div>

        <div v-if="filteredTemplates.length" class="template-grid">
          <button
            v-for="template in filteredTemplates"
            :key="template.id"
            class="template-card"
            type="button"
            @click="useTemplate(template)"
          >
            <div class="template-card-preview" :style="{ '--template-accent': template.accent }">
              <div class="template-mini-sheet">
                <span class="template-mini-kicker">{{ template.label }}</span>
                <strong>{{ template.title }}</strong>
                <i></i><i></i><i></i>
                <b></b><b></b>
              </div>
            </div>
            <div class="template-card-body">
              <div><strong>{{ template.title }}</strong><span>{{ template.questions.length }} 道题 · 约 {{ Math.max(2, Math.ceil(template.questions.length * .7)) }} 分钟</span></div>
              <p>{{ template.description }}</p>
              <span class="template-use">使用模板 <b>→</b></span>
            </div>
          </button>
        </div>
        <div v-else class="template-empty">
          <strong>没有匹配的模板</strong>
          <span>试试其他关键词或切换分类</span>
          <button type="button" @click="templateSearch = ''">清除搜索</button>
        </div>
      </div>
    </div>
  </section>

  <template v-else>
    <section class="editor-overview" aria-label="问卷概览">
      <div><span>当前结构</span><strong>{{ form.questions.length }} 道题</strong></div>
      <div><span>必填问题</span><strong>{{ requiredQuestionCount }} 道</strong></div>
      <div><span>最长填写</span><strong>{{ form.responseTimeoutMinutes }} 分钟</strong></div>
      <div class="editor-overview-source"><span>创建方式</span><strong>{{ selectedTemplateName || (form.id ? '已有问卷' : '空白问卷') }}</strong></div>
    </section>

    <div class="editor-grid">
      <section>
      <div class="card form-card"><label>表格基本信息</label><input v-model="form.title" class="title-input" maxlength="60" placeholder="请输入表格名称" /><textarea v-model="form.description" placeholder="写一段表格说明，让填写者了解调查目的" /><div class="meta-line">{{ form.questions.length }} 道题目 · 匿名填写 {{ form.anonymous ? '开启' : '关闭' }}</div></div>
      <div v-for="(question, index) in form.questions" :key="question.id || index" class="card question-card"><div class="question-top"><b>{{ String(index + 1).padStart(2, '0') }}</b><select v-model="question.type"><option v-for="item in types" :key="item[0]" :value="item[0]">{{ item[1] }}</option></select><button class="danger ghost" @click="form.questions.splice(index, 1)">删除</button></div><input v-model="question.title" class="question-title" placeholder="请输入问题标题" /><div v-if="question.type === 'single' || question.type === 'multiple'" class="options"><div v-for="(option, optionIndex) in question.options" :key="option.id || optionIndex" class="option-row"><span>{{ question.type === 'single' ? '○' : '□' }}</span><input v-model="option.label" :placeholder="`选项 ${optionIndex + 1}`" /><button class="ghost" @click="question.options.splice(optionIndex, 1)">×</button></div><button class="link-button" @click="question.options.push({ label: `选项 ${question.options.length + 1}`, sortOrder: question.options.length })">+ 添加选项</button></div><label class="switch-row"><input v-model="question.required" type="checkbox" />必填</label></div>
        <div class="quick-add-questions">
          <span>添加题目</span>
          <button v-for="item in types" :key="item[0]" type="button" @click="addQuestion(item[0])">
            <b>＋</b>{{ item[1] }}
          </button>
        </div>
      </section>

      <aside class="editor-side">
      <section v-if="isPublished" class="card share-side-card">
        <div class="share-side-head"><div><span>已发布</span><h3>填写链接</h3></div><button class="copy-icon-button" title="复制填写链接" @click="copyPublicUrl">{{ copied ? '已复制' : '复制' }}</button></div>
        <template v-if="shareUrl">
          <input class="share-url-input" :value="shareUrl" readonly @focus="selectShareUrl" />
          <div v-if="qrCodeUrl" class="share-side-qr"><img :src="qrCodeUrl" alt="问卷二维码" /><div><b>扫码填写</b><a :href="qrCodeUrl" :download="`${form.title || 'questionnaire'}-qrcode.png`">下载二维码</a></div></div>
        </template>
        <p v-else class="share-loading">正在读取已发布表格的分享信息，请刷新后重试。</p>
      </section>
      <section class="card appearance-card">
        <div class="appearance-heading"><div><h3>问卷背景</h3><p>公开填写页外观</p></div><button v-if="backgroundPreviewUrl" class="ghost danger" type="button" :disabled="backgroundUploading" @click="removeBackground">移除</button></div>
        <div class="background-preview" :class="{ empty: !backgroundPreviewUrl }" :style="backgroundPreviewStyle"><div><strong>{{ form.title || '问卷标题' }}</strong><span>{{ backgroundPreviewUrl ? '背景预览' : '默认浅色背景' }}</span></div></div>
        <label class="background-upload-button">
          <span>{{ backgroundUploading ? '正在保存...' : backgroundPreviewUrl ? '更换背景' : '选择背景' }}</span>
          <input type="file" accept="image/jpeg,image/png,image/webp" :disabled="backgroundUploading || saving" @change="selectBackground" />
        </label>
        <p class="setting-hint">JPG、PNG 或 WEBP，最大 5MB。</p>
      </section>
      <section class="card ai-card"><h3>AI 表格助手</h3><p>快速生成和优化表格</p><p class="ai-connection">DeepSeek · 后端安全调用</p><textarea v-model="aiPrompt" placeholder="例如：帮我生成一份员工满意度调查表，包含 8 道题..." /><button class="primary full" :disabled="aiLoading" @click="generateWithAi">{{ aiLoading ? '正在生成...' : '生成题目' }}</button></section>
      </aside>
    </div>
  </template>

  <Teleport to="body">
    <Transition name="settings-drawer">
      <div v-if="settingsOpen" class="settings-drawer-backdrop" @click.self="closeSettings()">
        <aside class="settings-drawer-panel" role="dialog" aria-modal="true" aria-labelledby="settings-drawer-title">
          <header class="settings-drawer-head">
            <div>
              <h2 id="settings-drawer-title">表格设置</h2>
              <p>配置收集状态与填写规则</p>
            </div>
            <button type="button" title="关闭设置" aria-label="关闭设置" :disabled="saving" @click="closeSettings()">×</button>
          </header>

          <div class="settings-drawer-body">
            <div class="settings-status-row">
              <div><strong>当前状态</strong><small>{{ isPublished ? '公开链接可正常填写' : form.status === 'closed' ? '公开链接已暂停访问' : '发布后才会开始收集' }}</small></div>
              <span :class="['collection-badge', form.status || 'draft']">{{ isPublished ? '收集中' : form.status === 'closed' ? '已停止' : '草稿' }}</span>
            </div>

            <section class="settings-section">
              <span class="settings-section-label">基础</span>
              <label class="setting-toggle-row">
                <span class="setting-toggle-copy"><strong>开启收集</strong><small>{{ form.id ? '关闭后公开链接将暂停访问' : '保存问卷后可开启' }}</small></span>
                <span class="setting-switch"><input type="checkbox" :checked="isPublished" :disabled="!form.id || collectionUpdating" @change="toggleCollection" /><i></i></span>
              </label>
              <label class="setting-toggle-row">
                <span class="setting-toggle-copy"><strong>允许匿名填写</strong><small>关闭后需填写姓名和邮箱</small></span>
                <span class="setting-switch"><input v-model="form.anonymous" type="checkbox" /><i></i></span>
              </label>
            </section>

            <section class="settings-section">
              <span class="settings-section-label">填写规则</span>
              <label class="setting-toggle-row">
                <span class="setting-toggle-copy"><strong>每人限填一次</strong><small>{{ form.anonymous ? '匿名问卷按访问地址校验' : '实名问卷按邮箱校验' }}</small></span>
                <span class="setting-switch"><input v-model="form.oneResponse" type="checkbox" /><i></i></span>
              </label>
              <label class="setting-number-row">
                <span><strong>最长填写时间</strong><small>超过时间将记为未完成</small></span>
                <span class="setting-number-control"><input v-model.number="form.responseTimeoutMinutes" type="number" min="1" max="1440" step="1" /><b>分钟</b></span>
              </label>
            </section>

            <section class="settings-section">
              <span class="settings-section-label">提交后</span>
              <label class="setting-toggle-row">
                <span class="setting-toggle-copy"><strong>显示答卷结果</strong><small>提交后展示本次填写内容</small></span>
                <span class="setting-switch"><input v-model="form.showResult" type="checkbox" /><i></i></span>
              </label>
            </section>
          </div>

          <footer class="settings-drawer-footer">
            <button type="button" :disabled="saving" @click="closeSettings()">取消</button>
            <button class="primary" type="button" :disabled="saving" @click="saveSettings">{{ saving ? '保存中...' : '保存设置' }}</button>
          </footer>
        </aside>
      </div>
    </Transition>

    <div v-if="previewOpen" class="survey-preview" role="dialog" aria-modal="true" aria-label="问卷预览">
      <header class="survey-preview-toolbar">
        <div class="survey-preview-heading">
          <strong>问卷预览</strong>
          <span>当前未保存的修改也会显示</span>
        </div>
        <div class="survey-preview-actions">
          <div class="preview-viewport-switch" aria-label="预览宽度">
            <button type="button" :class="{ active: previewViewport === 'desktop' }" @click="previewViewport = 'desktop'">电脑</button>
            <button type="button" :class="{ active: previewViewport === 'mobile' }" @click="previewViewport = 'mobile'">手机</button>
          </div>
          <button class="survey-preview-close" type="button" title="关闭预览" aria-label="关闭预览" @click="closePreview">×</button>
        </div>
      </header>

      <main class="survey-preview-stage">
        <div
          class="survey-preview-page"
          :class="{
            mobile: previewViewport === 'mobile',
            'has-background': backgroundPreviewUrl,
          }"
          :style="previewPageStyle"
        >
          <article class="survey-preview-form">
            <h1>{{ form.title.trim() || '未命名问卷' }}</h1>
            <p>{{ form.description?.trim() || '暂无问卷说明' }}</p>

            <section v-if="!form.anonymous" class="preview-identity-fields">
              <h2>填写者信息</h2>
              <label>姓名<input type="text" readonly placeholder="请输入姓名" /></label>
              <label>邮箱<input type="email" readonly placeholder="请输入邮箱" /></label>
            </section>

            <section v-for="(question, index) in form.questions" :key="question.id || index" class="survey-preview-question">
              <h3>
                {{ index + 1 }}. {{ question.title.trim() || '未填写题目标题' }}
                <small v-if="question.required">* 必填</small>
              </h3>
              <div v-if="question.type === 'single' || question.type === 'multiple'" class="preview-options">
                <div v-for="(option, optionIndex) in question.options" :key="option.id || optionIndex" class="preview-option">
                  <span>{{ question.type === 'single' ? '○' : '□' }}</span>
                  {{ option.label.trim() || `选项 ${optionIndex + 1}` }}
                </div>
                <div v-if="!question.options.length" class="preview-empty-option">暂无选项</div>
              </div>
              <input v-else-if="question.type === 'date'" type="date" readonly />
              <input v-else-if="question.type === 'rating'" type="number" min="1" max="5" readonly placeholder="1 - 5" />
              <input v-else-if="question.type === 'number'" type="number" readonly placeholder="请输入数字" />
              <input v-else-if="question.type === 'phone'" type="tel" readonly placeholder="请输入电话号码" />
              <textarea v-else readonly placeholder="请输入回答"></textarea>
            </section>

            <div v-if="!form.questions.length" class="survey-preview-empty">暂未添加题目</div>
            <button class="primary survey-preview-submit" type="button" disabled>提交答卷</button>
            <p class="survey-preview-note">预览模式不会提交或保存任何答卷</p>
          </article>
        </div>
      </main>
    </div>
  </Teleport>
</template>

<style scoped>
.template-library {
  width: 100%;
  max-width: none;
  margin: 0 auto;
}

.template-page-header {
  width: 100%;
  max-width: none;
  margin-right: auto;
  margin-left: auto;
}

.template-start-band {
  display: flex;
  min-height: 142px;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  margin-bottom: 18px;
  padding: 25px 28px;
  border: 1px solid #314c47;
  border-radius: 8px;
  color: #f7f9ff;
  background: #263e3a;
}

.template-start-copy {
  min-width: 0;
}

.template-eyebrow {
  display: block;
  margin-bottom: 8px;
  color: #a7c9c1;
  font-size: 10px;
  font-weight: 800;
}

.template-start-copy h2 {
  margin: 0 0 8px;
  color: #fff;
  font-size: 22px;
}

.template-start-copy p {
  margin: 0;
  color: #c5d6d2;
  line-height: 1.6;
}

.blank-template-button {
  display: flex;
  flex: 0 0 280px;
  min-height: 82px;
  align-items: center;
  gap: 15px;
  padding: 15px 18px;
  border-color: #ffffff26;
  color: #243457;
  background: #fff;
  text-align: left;
}

.blank-template-button:hover {
  border-color: #aec3ec;
  color: #315db3;
  transform: translateY(-1px);
}

.blank-template-icon {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  place-items: center;
  border-radius: 6px;
  color: #fff;
  background: #4779d7;
  font-size: 24px;
  line-height: 1;
}

.blank-template-button strong,
.blank-template-button small {
  display: block;
}

.blank-template-button strong {
  margin-bottom: 5px;
  font-size: 14px;
}

.blank-template-button small {
  color: #8995aa;
  font-size: 11px;
}

.template-browser {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  min-height: 610px;
  overflow: hidden;
  border: 1px solid #dde3ea;
  border-radius: 8px;
  background: #fff;
}

.template-categories {
  padding: 24px 14px;
  border-right: 1px solid #e7ebf2;
  background: #f6f7f9;
}

.template-categories > strong {
  display: block;
  padding: 0 12px 13px;
  color: #8590a5;
  font-size: 11px;
}

.template-categories button {
  width: 100%;
  min-height: 40px;
  margin: 2px 0;
  padding: 9px 12px;
  border: 0;
  color: #53617a;
  background: transparent;
  text-align: left;
}

.template-categories button:hover {
  color: #2f625a;
  background: #eaf1ef;
}

.template-categories button.active {
  color: #28584f;
  background: #e3eeeb;
  font-weight: 750;
}

.template-results {
  min-width: 0;
  padding: 25px 26px 32px;
}

.template-results-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 21px;
}

.template-results-head h2 {
  display: inline;
  margin: 0;
  color: #24324e;
  font-size: 19px;
}

.template-results-head > div > span {
  margin-left: 10px;
  color: #97a1b4;
  font-size: 11px;
}

.template-search {
  display: flex;
  width: min(100%, 240px);
  min-height: 38px;
  align-items: center;
  gap: 7px;
  margin: 0;
  padding: 0 11px;
  border: 1px solid #dde4ee;
  border-radius: 6px;
  color: #8995aa;
  background: #fbfcfe;
}

.template-search:focus-within {
  border-color: #7497dc;
  box-shadow: 0 0 0 3px #527cd317;
}

.template-search > span {
  flex: 0 0 auto;
  font-size: 20px;
  line-height: 1;
}

.template-search input {
  height: 36px;
  min-width: 0;
  padding: 0;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 12px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.template-card {
  min-width: 0;
  overflow: hidden;
  padding: 0;
  border: 1px solid #e1e7f0;
  border-radius: 8px;
  background: #fff;
  text-align: left;
  transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
}

.template-card:hover {
  border-color: #8daaa4;
  color: inherit;
  box-shadow: 0 10px 24px #233a6a17;
  transform: translateY(-2px);
}

.template-card-preview {
  display: grid;
  min-height: 158px;
  place-items: center;
  overflow: hidden;
  padding: 19px;
  background: color-mix(in srgb, var(--template-accent) 12%, #f7f9fc);
}

.template-mini-sheet {
  display: block;
  width: min(100%, 170px);
  min-height: 123px;
  padding: 15px 14px;
  border-top: 4px solid var(--template-accent);
  border-radius: 4px;
  color: #26344f;
  background: #fff;
  box-shadow: 0 8px 20px #233a6a17;
}

.template-mini-kicker {
  display: block;
  margin-bottom: 7px;
  color: var(--template-accent);
  font-size: 8px;
  font-weight: 800;
}

.template-mini-sheet strong {
  display: block;
  overflow: hidden;
  margin-bottom: 12px;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-mini-sheet i {
  display: block;
  width: 100%;
  height: 5px;
  margin: 8px 0;
  border-radius: 2px;
  background: #e8edf4;
}

.template-mini-sheet i:nth-of-type(2) {
  width: 78%;
}

.template-mini-sheet i:nth-of-type(3) {
  width: 88%;
}

.template-mini-sheet b {
  display: inline-block;
  width: 36%;
  height: 9px;
  margin: 2px 5px 0 0;
  border: 1px solid color-mix(in srgb, var(--template-accent) 35%, #dce3ed);
  border-radius: 2px;
  background: color-mix(in srgb, var(--template-accent) 7%, #fff);
}

.template-card-body {
  padding: 16px 16px 15px;
}

.template-card-body > div {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.template-card-body strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #293752;
  font-size: 14px;
}

.template-card-body > div > span {
  flex: 0 0 auto;
  color: #98a3b7;
  font-size: 9px;
  white-space: nowrap;
}

.template-card-body p {
  min-height: 40px;
  margin: 9px 0 13px;
  color: #7f8ba1;
  font-size: 11px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.template-use {
  color: #327064;
  font-size: 11px;
  font-weight: 750;
}

.template-use b {
  margin-left: 4px;
  font-size: 14px;
}

.template-empty {
  display: grid;
  min-height: 360px;
  place-content: center;
  justify-items: center;
  gap: 8px;
  color: #8b97ab;
  text-align: center;
}

.template-empty strong {
  color: #53617b;
}

.template-empty button {
  margin-top: 7px;
  color: #3d6fbe;
  background: #f6f9ff;
}

.editor-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(130px, .7fr)) minmax(190px, 1.4fr);
  width: 100%;
  max-width: none;
  margin: 0 auto 18px;
  overflow: hidden;
  border: 1px solid #e2e8f1;
  border-radius: 8px;
  background: #fff;
}

.editor-overview > div {
  min-width: 0;
  padding: 14px 18px;
  border-right: 1px solid #e9edf4;
}

.editor-overview > div:last-child {
  border-right: 0;
}

.editor-overview span,
.editor-overview strong {
  display: block;
}

.editor-overview span {
  margin-bottom: 5px;
  color: #919caf;
  font-size: 10px;
}

.editor-overview strong {
  overflow: hidden;
  color: #34435f;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editor-overview-source {
  background: #f8faff;
}

.quick-add-questions {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  padding: 15px;
  border: 1px dashed #cfd9e9;
  border-radius: 8px;
  background: #f9fbfe;
}

.quick-add-questions > span {
  grid-column: 1 / -1;
  margin-bottom: 2px;
  color: #7b879d;
  font-size: 11px;
  font-weight: 750;
}

.quick-add-questions button {
  display: flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 8px;
  color: #526381;
  background: #fff;
  font-size: 11px;
  white-space: nowrap;
}

.quick-add-questions button:hover {
  color: #315fb3;
  background: #f3f7ff;
}

.quick-add-questions b {
  color: #4f7cce;
  font-size: 15px;
  line-height: 1;
}

.settings-drawer-backdrop {
  position: fixed;
  z-index: 900;
  inset: 0;
  background: #17213d52;
}

.settings-drawer-panel {
  position: absolute;
  top: 0;
  right: 0;
  display: grid;
  width: min(100%, 400px);
  height: 100%;
  grid-template-rows: auto minmax(0, 1fr) auto;
  color: #273550;
  background: #fff;
  box-shadow: -12px 0 36px #17213d24;
}

.settings-drawer-head {
  display: flex;
  min-height: 72px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  border-bottom: 1px solid #e7ebf2;
}

.settings-drawer-head h2 {
  margin: 0;
  font-size: 18px;
}

.settings-drawer-head p {
  margin: 4px 0 0;
  color: #8b97ad;
  font-size: 11px;
}

.settings-drawer-head button {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  padding: 0;
  place-items: center;
  border: 0;
  color: #66748b;
  background: transparent;
  font-size: 24px;
  line-height: 1;
}

.settings-drawer-head button:hover {
  background: #f2f5f9;
}

.settings-drawer-body {
  overflow-y: auto;
  padding: 8px 20px 24px;
}

.settings-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 8px 0 2px;
  padding: 14px;
  border: 1px solid #e5eaf2;
  border-radius: 7px;
  background: #f8f9fc;
}

.settings-status-row > div {
  min-width: 0;
}

.settings-status-row strong,
.settings-status-row small {
  display: block;
}

.settings-status-row strong {
  color: #43516b;
  font-size: 13px;
}

.settings-status-row small {
  margin-top: 4px;
  color: #8d98aa;
  font-size: 10px;
  line-height: 1.5;
}

.settings-drawer-footer {
  display: flex;
  min-height: 68px;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid #e7ebf2;
  background: #fff;
}

.settings-drawer-footer button {
  min-width: 88px;
}

.settings-drawer-enter-active,
.settings-drawer-leave-active {
  transition: background-color .2s ease;
}

.settings-drawer-enter-active .settings-drawer-panel,
.settings-drawer-leave-active .settings-drawer-panel {
  transition: transform .22s ease;
}

.settings-drawer-enter-from,
.settings-drawer-leave-to {
  background-color: transparent;
}

.settings-drawer-enter-from .settings-drawer-panel,
.settings-drawer-leave-to .settings-drawer-panel {
  transform: translateX(100%);
}

.collection-badge {
  flex: 0 0 auto;
  padding: 4px 7px;
  border-radius: 4px;
  color: #7a8496;
  background: #eef1f5;
  font-size: 10px;
  font-weight: 750;
}

.collection-badge.active {
  color: #287450;
  background: #e6f5ec;
}

.collection-badge.closed {
  color: #a44f5a;
  background: #fcecef;
}

.settings-section {
  padding: 17px 0 4px;
  border-top: 1px solid #e9edf3;
}

.settings-status-row + .settings-section {
  border-top: 0;
}

.settings-section-label {
  display: block;
  margin-bottom: 6px;
  color: #8c97aa;
  font-size: 10px;
  font-weight: 750;
}

.setting-toggle-row,
.setting-number-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0;
  padding: 11px 0;
  color: #485872;
}

.setting-toggle-copy,
.setting-number-row > span:first-child {
  min-width: 0;
}

.setting-toggle-copy strong,
.setting-toggle-copy small,
.setting-number-row strong,
.setting-number-row small {
  display: block;
}

.setting-toggle-copy strong,
.setting-number-row strong {
  color: #43516b;
  font-size: 12px;
}

.settings-drawer-panel .setting-toggle-copy strong,
.settings-drawer-panel .setting-number-row strong {
  font-size: 13px;
}

.setting-toggle-copy small,
.setting-number-row small {
  margin-top: 4px;
  color: #929caf;
  font-size: 9px;
  line-height: 1.5;
}

.setting-switch {
  position: relative;
  display: block;
  width: 38px;
  height: 22px;
  flex: 0 0 38px;
}

.setting-switch input {
  position: absolute;
  z-index: 2;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.setting-switch i {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: #cfd5de;
  transition: background .18s ease;
}

.setting-switch i::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px #1e2a3b2e;
  transition: transform .18s ease;
}

.setting-switch input:checked + i {
  background: #3f73d8;
}

.setting-switch input:checked + i::after {
  transform: translateX(16px);
}

.setting-switch input:focus-visible + i {
  box-shadow: 0 0 0 3px #3f73d829;
}

.setting-switch input:disabled + i {
  opacity: .55;
}

.setting-number-control {
  display: flex;
  flex: 0 0 98px;
  align-items: center;
  overflow: hidden;
  border: 1px solid #dce3ed;
  border-radius: 6px;
  background: #fff;
}

.setting-number-control input {
  width: 58px;
  height: 36px;
  padding: 7px 4px 7px 9px;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 12px;
}

.setting-number-control b {
  color: #8b96a8;
  font-size: 10px;
  font-weight: 500;
}

.survey-preview {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: grid;
  grid-template-rows: 64px minmax(0, 1fr);
  color: #17213d;
  background: #e9edf3;
}

.survey-preview-toolbar {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 22px;
  border-bottom: 1px solid #d9e0e9;
  background: #fff;
  box-shadow: 0 2px 12px #18213d12;
}

.survey-preview-heading {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: 12px;
}

.survey-preview-heading strong {
  color: #263653;
  font-size: 16px;
}

.survey-preview-heading span {
  overflow: hidden;
  color: #8a96aa;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.survey-preview-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 12px;
}

.preview-viewport-switch {
  display: grid;
  grid-template-columns: repeat(2, 58px);
  padding: 3px;
  border: 1px solid #dce3ed;
  border-radius: 6px;
  background: #f4f6f9;
}

.preview-viewport-switch button {
  height: 30px;
  padding: 0;
  border: 0;
  color: #718097;
  background: transparent;
  font-size: 12px;
}

.preview-viewport-switch button.active {
  color: #315db3;
  background: #fff;
  box-shadow: 0 1px 5px #22355c17;
}

.survey-preview-close {
  display: grid;
  width: 36px;
  height: 36px;
  padding: 0;
  place-items: center;
  border: 0;
  color: #5d6a80;
  background: transparent;
  font-size: 25px;
  line-height: 1;
}

.survey-preview-stage {
  overflow: auto;
  padding: 30px;
}

.survey-preview-page {
  width: min(100%, 980px);
  min-height: calc(100vh - 124px);
  margin: 0 auto;
  padding: 42px 18px;
  background: #f4f6fa;
  transition: width .2s ease;
}

.survey-preview-page.mobile {
  width: min(100%, 390px);
  min-height: 720px;
  padding: 20px 10px;
  box-shadow: 0 16px 44px #1c294329;
}

.survey-preview-page.has-background {
  background-color: #dfe5ed;
  background-image: linear-gradient(#18213859, #18213859), var(--editor-preview-background);
  background-position: center;
  background-size: cover;
}

.survey-preview-form {
  width: min(100%, 780px);
  margin: auto;
  padding: 34px;
  border: 1px solid #e5eaf3;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 10px #25386b08;
}

.has-background .survey-preview-form {
  border-color: #ffffffa8;
  background: #fffffff2;
  box-shadow: 0 18px 50px #10182b40;
  backdrop-filter: blur(8px);
}

.survey-preview-form > h1 {
  overflow-wrap: anywhere;
  color: #17213d;
  text-align: center;
}

.survey-preview-form > p {
  margin: 12px 0 32px;
  color: #7f8aa3;
  line-height: 1.7;
  text-align: center;
  overflow-wrap: anywhere;
}

.preview-identity-fields {
  margin-bottom: 18px;
  padding: 18px;
  border: 1px solid #e5eaf3;
  border-radius: 7px;
  background: #fafbfe;
}

.preview-identity-fields h2 {
  margin-bottom: 14px;
  font-size: 17px;
}

.preview-identity-fields label {
  max-width: 460px;
  margin-bottom: 12px;
}

.survey-preview-question {
  padding: 22px 0;
  border-top: 1px solid #edf0f5;
}

.survey-preview-question h3 {
  margin: 0 0 14px;
  color: #293754;
  font-size: 16px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.survey-preview-question h3 small {
  color: #d95665;
  font-size: 12px;
  white-space: nowrap;
}

.preview-options {
  display: grid;
  gap: 9px;
}

.preview-option {
  min-height: 40px;
  padding: 10px 13px;
  border: 1px solid #dbe2f0;
  border-radius: 6px;
  color: #34405e;
  background: #fff;
  overflow-wrap: anywhere;
}

.preview-option span {
  margin-right: 7px;
  color: #91a0bd;
  font-size: 17px;
}

.preview-empty-option,
.survey-preview-empty {
  color: #98a2b6;
  text-align: center;
}

.survey-preview-empty {
  padding: 38px 10px;
  border-top: 1px solid #edf0f5;
}

.survey-preview-submit {
  width: 100%;
}

.survey-preview-submit:disabled {
  cursor: not-allowed;
  opacity: .72;
}

.survey-preview-form > .survey-preview-note {
  margin: 10px 0 0;
  color: #98a2b6;
  font-size: 11px;
}

.mobile .survey-preview-form {
  padding: 22px 16px;
}

.mobile .preview-identity-fields {
  padding: 14px;
}

@media (max-width: 620px) {
  .template-start-band {
    display: block;
    padding: 21px;
  }

  .blank-template-button {
    width: 100%;
    margin-top: 20px;
  }

  .template-browser {
    display: block;
  }

  .template-categories {
    display: flex;
    overflow-x: auto;
    gap: 5px;
    padding: 12px;
    border-right: 0;
    border-bottom: 1px solid #e7ebf2;
  }

  .template-categories > strong {
    display: none;
  }

  .template-categories button {
    width: auto;
    flex: 0 0 auto;
    margin: 0;
  }

  .template-results {
    padding: 19px 15px 24px;
  }

  .template-results-head {
    align-items: stretch;
    flex-direction: column;
  }

  .template-search {
    width: 100%;
  }

  .template-grid {
    grid-template-columns: 1fr;
  }

  .editor-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .editor-overview > div:nth-child(2) {
    border-right: 0;
  }

  .editor-overview > div:nth-child(-n + 2) {
    border-bottom: 1px solid #e9edf4;
  }

  .quick-add-questions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .survey-preview {
    grid-template-rows: auto minmax(0, 1fr);
  }

  .survey-preview-toolbar {
    min-height: 58px;
    padding: 9px 12px;
  }

  .survey-preview-heading span {
    display: none;
  }

  .preview-viewport-switch {
    grid-template-columns: repeat(2, 48px);
  }

  .survey-preview-stage {
    padding: 12px;
  }

  .survey-preview-page,
  .survey-preview-page.mobile {
    min-height: calc(100vh - 82px);
  }
}

@media (min-width: 621px) and (max-width: 1050px) {
  .template-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1500px) {
  .template-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
