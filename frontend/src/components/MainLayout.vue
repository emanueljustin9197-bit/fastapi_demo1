<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { BarChart3, Download, FilePlus2, Files, LogOut, Settings, TableProperties } from 'lucide-vue-next'
import { authApi } from '../api/auth'
import { apiFetch, assetUrl, AUTH_EXPIRED_EVENT } from '../api/client'
import type { UserInfo } from '../types'
import SurveyEditor from '../views/SurveyEditor.vue'
import QuestionnaireList from '../views/QuestionnaireList.vue'
import AnalysisPage from '../views/AnalysisPage.vue'
import ExportPage from '../views/ExportPage.vue'
import SettingsPage from '../views/SettingsPage.vue'

const props = defineProps<{ token: string }>()
const emit = defineEmits<{ 'update:token': [string] }>()
const page = ref<'create' | 'list' | 'analysis' | 'export' | 'settings'>('list')
const editingId = ref<number | null>(null)
const selectedId = ref<number | null>(null)
const loggedIn = computed(() => Boolean(props.token))
const authMode = ref<'login' | 'register'>('login')
const authError = ref('')
const submitting = ref(false)
const showPassword = ref(false)
const user = ref<UserInfo>({})
const avatarBroken = ref(false)
const userInitial = computed(() => (user.value.name || user.value.email || '我').trim().slice(0, 1).toUpperCase())
const userAvatar = computed(() => assetUrl(user.value.avatar))

function logout() {
  localStorage.removeItem('survey_token')
  localStorage.removeItem('survey_user')
  emit('update:token', '')
  page.value = 'list'
}

function applyUser(value: UserInfo) {
  user.value = value
  avatarBroken.value = false
}

function handleUserUpdated(event: Event) {
  applyUser((event as CustomEvent<UserInfo>).detail)
}

function handleAuthExpired(event: Event) {
  const detail = (event as CustomEvent<{ message?: string }>).detail
  applyUser({})
  authMode.value = 'login'
  authError.value = detail?.message || '登录已失效，请重新登录'
  page.value = 'list'
  emit('update:token', '')
}

async function loadUser() {
  const cached = localStorage.getItem('survey_user')
  if (cached) {
    try { applyUser(JSON.parse(cached) as UserInfo) } catch { localStorage.removeItem('survey_user') }
  }
  if (!props.token) return
  try {
    const account = await authApi.info(props.token)
    applyUser(account)
    localStorage.setItem('survey_user', JSON.stringify(account))
  } catch {
    // Login remains usable even when optional profile data is temporarily unavailable.
  }
}

function createNew() {
  editingId.value = null
  page.value = 'create'
}

function edit(id: number) {
  editingId.value = id
  page.value = 'create'
}

function analyze(id: number) {
  selectedId.value = id
  page.value = 'analysis'
}

function switchAuthMode() {
  authMode.value = authMode.value === 'login' ? 'register' : 'login'
  authError.value = ''
  showPassword.value = false
}

async function submitAuth(event: Event) {
  const form = event.target as HTMLFormElement
  const data = new FormData(form)
  authError.value = ''
  submitting.value = true
  try {
    const email = String(data.get('email') || '').trim()
    const password = String(data.get('password') || '')
    const result = authMode.value === 'login'
      ? await authApi.login(email, password)
      : await authApi.register(String(data.get('name') || '').trim(), email, password)
    localStorage.setItem('survey_token', result.token)
    emit('update:token', result.token)
  } catch (error) {
    authError.value = (error as Error).message
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  window.addEventListener('survey-user-updated', handleUserUpdated)
  window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired)
  loadUser()
})

watch(() => props.token, (token) => {
  if (token) loadUser()
})

onUnmounted(() => {
  window.removeEventListener('survey-user-updated', handleUserUpdated)
  window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired)
})
</script>

<template>
  <div v-if="!loggedIn" class="auth-screen">
    <section class="auth-visual" aria-label="在线表格工作台">
      <div class="auth-brand">
        <span class="auth-brand-mark">▦</span>
        <span>在线表格</span>
      </div>
      <div class="auth-visual-copy">
        <p class="auth-kicker">FORM WORKSPACE / 01</p>
        <h2>让每一次回答，<br /><em>都变成清晰洞察。</em></h2>
        <p>从设计问卷、回收答卷到数据分析，在一个安静而高效的工作台完成完整流程。</p>
      </div>
      <div class="auth-visual-footer">
        <span class="auth-status-dot"></span>
        <span>你的数据，始终在你的掌控中</span>
        <span class="auth-footer-line"></span>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-panel-inner">
        <div class="auth-mobile-brand">
          <span class="auth-brand-mark">▦</span>
          <span>在线表格</span>
        </div>
        <div class="auth-heading">
          <p class="auth-kicker">WELCOME BACK</p>
          <h1>{{ authMode === 'login' ? '欢迎回来' : '创建你的工作台' }}</h1>
          <p>{{ authMode === 'login' ? '登录后继续管理你的问卷与数据。' : '注册一个账号，开始创建第一份问卷。' }}</p>
        </div>
        <form class="auth-form" @submit.prevent="submitAuth">
          <label v-if="authMode === 'register'" class="auth-field">
            <span>显示名称</span>
            <span class="auth-input-wrap">
              <span class="auth-input-icon">●</span>
              <input name="name" autocomplete="name" placeholder="请输入你的称呼" required />
            </span>
          </label>
          <label class="auth-field">
            <span>登录邮箱</span>
            <span class="auth-input-wrap">
              <span class="auth-input-icon">@</span>
              <input name="email" type="email" autocomplete="email" placeholder="name@company.com" required />
            </span>
          </label>
          <label class="auth-field">
            <span>密码</span>
            <span class="auth-input-wrap">
              <span class="auth-input-icon">●</span>
              <input
                name="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="至少 6 位字符"
                minlength="6"
                required
              />
              <button class="password-toggle" type="button" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </span>
          </label>
          <button class="auth-submit" type="submit" :disabled="submitting">
            <span v-if="submitting" class="auth-spinner"></span>
            {{ submitting ? '正在处理...' : authMode === 'login' ? '登录工作台' : '注册并登录' }}
            <span v-if="!submitting" class="auth-submit-arrow">→</span>
          </button>
        </form>
        <div v-if="authError" class="auth-error" role="alert">
          <span>!</span>{{ authError }}
        </div>
        <div class="auth-switch">
          <span>{{ authMode === 'login' ? '还没有账号？' : '已经有账号？' }}</span>
          <button type="button" @click="switchAuthMode">
            {{ authMode === 'login' ? '立即注册' : '返回登录' }}
          </button>
        </div>
        <p class="auth-note">继续使用即表示你同意工作台的服务条款与隐私说明。</p>
      </div>
    </section>
  </div>

  <div v-else class="app-shell">
    <header class="topbar">
      <div class="brand">
        <TableProperties class="brand-icon" :size="24" :stroke-width="1.8" aria-hidden="true" />
        <div><strong>在线表格</strong><small>ONLINE FORM</small></div>
      </div>
      <nav class="topbar-nav" aria-label="工作台导航">
        <button title="创建表格" :class="{ active: page === 'create' }" @click="createNew">
          <FilePlus2 class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" /><span>创建表格<small>设计与发布新表格</small></span>
        </button>
        <button title="我的表格" :class="{ active: page === 'list' }" @click="page = 'list'">
          <Files class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" /><span>我的表格<small>管理已创建的表格</small></span>
        </button>
        <button title="表格分析" :class="{ active: page === 'analysis' }" @click="page = 'analysis'">
          <BarChart3 class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" /><span>表格分析<small>查看填写与统计结果</small></span>
        </button>
        <button title="导出数据" :class="{ active: page === 'export' }" @click="page = 'export'">
          <Download class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" /><span>导出数据<small>下载 Excel、CSV 或 JSON</small></span>
        </button>
        <button title="账号设置" :class="{ active: page === 'settings' }" @click="page = 'settings'">
          <Settings class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" /><span>设置<small>账号与登录</small></span>
        </button>
      </nav>
      <div class="topbar-account">
        <button class="topbar-user" type="button" title="账号设置" @click="page = 'settings'">
          <span class="sidebar-avatar">
            <img v-if="userAvatar && !avatarBroken" :src="userAvatar" alt="用户头像" @error="avatarBroken = true" />
            <span v-else>{{ userInitial }}</span>
          </span>
          <span class="topbar-user-copy"><strong>{{ user.name || '当前账号' }}</strong><small>{{ user.email || '已登录' }}</small></span>
        </button>
        <button class="topbar-logout" type="button" title="退出登录" aria-label="退出登录" @click="logout"><LogOut :size="18" :stroke-width="1.8" aria-hidden="true" /></button>
      </div>
    </header>
    <main class="main-content">
      <SurveyEditor v-if="page === 'create'" :token="token" :questionnaire-id="editingId" @saved="page = 'list'" />
      <QuestionnaireList v-if="page === 'list'" :token="token" @create="createNew" @edit="edit" @analyze="analyze" />
      <KeepAlive>
        <AnalysisPage v-if="page === 'analysis'" :token="token" :questionnaire-id="selectedId" />
      </KeepAlive>
      <ExportPage v-if="page === 'export'" :token="token" />
      <SettingsPage v-if="page === 'settings'" :token="token" />
    </main>
  </div>
</template>
