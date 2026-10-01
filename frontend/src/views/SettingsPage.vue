<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { authApi } from '../api/auth'
import { assetUrl } from '../api/client'
import type { UserInfo } from '../types'

const props = defineProps<{ token: string }>()
const user = ref<UserInfo>({})
const loading = ref(false)
const uploading = ref(false)
const error = ref('')
const saved = ref(false)
const avatarBroken = ref(false)

const initials = computed(() => (user.value.name || user.value.email || '我').trim().slice(0, 1).toUpperCase())
const avatar = computed(() => assetUrl(user.value.avatar))

function syncUser() {
  localStorage.setItem('survey_user', JSON.stringify(user.value))
  window.dispatchEvent(new CustomEvent('survey-user-updated', { detail: user.value }))
}

async function load() {
  try {
    user.value = await authApi.info(props.token)
    syncUser()
  } catch (loadError) {
    error.value = (loadError as Error).message
  }
}

async function save() {
  loading.value = true
  error.value = ''
  try {
    user.value = await authApi.update({
      name: user.value.name || '',
      phone: user.value.phone || '',
      company: user.value.company || '',
    }, props.token)
    syncUser()
    saved.value = true
    window.setTimeout(() => { saved.value = false }, 1800)
  } catch (saveError) {
    error.value = (saveError as Error).message
  } finally {
    loading.value = false
  }
}

async function uploadAvatar(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    error.value = '请选择图片文件'
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    error.value = '头像图片不能超过 5MB'
    return
  }
  uploading.value = true
  error.value = ''
  try {
    user.value = await authApi.uploadAvatar(file, props.token)
    avatarBroken.value = false
    syncUser()
  } catch (uploadError) {
    error.value = (uploadError as Error).message
  } finally {
    uploading.value = false
    input.value = ''
  }
}

onMounted(load)
</script>

<template>
  <header class="page-header settings-heading">
    <div><h1>账号设置</h1><p>管理你的个人资料、头像与工作账号信息</p></div>
    <span class="account-state"><i></i>账号正常</span>
  </header>

  <section class="settings-profile card">
    <div class="profile-avatar-area">
      <div class="profile-avatar">
        <img v-if="avatar && !avatarBroken" :src="avatar" alt="用户头像" @error="avatarBroken = true" />
        <span v-else>{{ initials }}</span>
      </div>
      <div><h2>{{ user.name || '未设置名称' }}</h2><p>{{ user.email || '登录邮箱未加载' }}</p></div>
    </div>
    <label class="avatar-upload modern-upload">
      <span>{{ uploading ? '上传中...' : '更换头像' }}</span>
      <small>JPG、PNG 或 WEBP，最大 5MB</small>
      <input type="file" accept="image/png,image/jpeg,image/webp" :disabled="uploading" @change="uploadAvatar" />
    </label>
  </section>

  <div v-if="error" class="error settings-error">{{ error }}</div>
  <div class="settings-layout">
    <section class="card profile-form-card">
      <div class="section-title"><div><h2>个人资料</h2><p>这些信息会显示在你的工作账号中</p></div></div>
      <div class="form-grid profile-form-grid">
        <label>显示名称<input v-model="user.name" maxlength="100" placeholder="请输入显示名称" /></label>
        <label>登录邮箱<input v-model="user.email" disabled /></label>
        <label>手机号码<input v-model="user.phone" maxlength="30" placeholder="选填" /></label>
        <label>所属组织<input v-model="user.company" maxlength="100" placeholder="选填" /></label>
      </div>
      <div class="form-footer"><span v-if="saved" class="success">资料已保存</span><span v-else>修改后会同步到当前账号</span><button class="primary" :disabled="loading" @click="save">{{ loading ? '保存中...' : '保存资料' }}</button></div>
    </section>

    <aside class="account-side">
      <section class="card account-panel">
        <h2>账号概览</h2>
        <div class="account-line"><span>账号类型</span><b>个人工作区</b></div>
        <div class="account-line"><span>登录方式</span><b>邮箱密码</b></div>
        <div class="account-line"><span>头像状态</span><b>{{ avatar ? '已设置' : '默认头像' }}</b></div>
      </section>
      <section class="account-tip"><strong>资料完善度</strong><div class="completion-bar"><i :style="{ width: `${[user.name, user.phone, user.company, user.avatar].filter(Boolean).length * 25}%` }"></i></div><p>完善资料后，团队协作时更容易识别你的账号。</p></section>
    </aside>
  </div>
</template>
