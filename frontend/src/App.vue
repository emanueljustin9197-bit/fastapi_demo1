<script setup lang="ts">
import { computed, ref } from 'vue'
import MainLayout from './components/MainLayout.vue'
import PublicSurvey from './views/PublicSurvey.vue'

const publicCode = computed(() => {
  const match = window.location.pathname.match(/^\/s\/([^/]+)/)
  return match?.[1] || ''
})
const token = ref(localStorage.getItem('survey_token') || '')
</script>

<template>
  <PublicSurvey v-if="publicCode" :public-code="publicCode" />
  <MainLayout v-else v-model:token="token" />
</template>

