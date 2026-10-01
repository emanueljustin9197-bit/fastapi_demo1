import { apiFetch, queryString } from './client'
import type { Questionnaire } from '../types'

export interface QuestionnaireListResult {
  list: Questionnaire[]
  total: number
  hasMore?: boolean
}

export const questionnaireApi = {
  statistics: (token: string) =>
    apiFetch<Record<string, number>>('/api/questionnaire/statistics', {}, token),

  list: (params: Record<string, unknown>, token: string) =>
    apiFetch<QuestionnaireListResult>(
      `/api/questionnaire/list${queryString(params)}`,
      {},
      token,
    ),

  detail: (id: number, token: string) =>
    apiFetch<Questionnaire>(`/api/questionnaire/detail?id=${id}`, {}, token),

  create: (payload: Questionnaire, token: string) =>
    apiFetch<{ id: number }>('/api/questionnaire/create', {
      method: 'POST',
      body: JSON.stringify(serializeQuestionnaire(payload)),
    }, token),

  update: (payload: Questionnaire, token: string) =>
    apiFetch<{ id: number }>('/api/questionnaire/update', {
      method: 'PUT',
      body: JSON.stringify({ id: payload.id, ...serializeQuestionnaire(payload) }),
    }, token),

  uploadBackground: (id: number, file: File, token: string) => {
    const form = new FormData()
    form.append('file', file)
    return apiFetch<{ backgroundImage: string }>(
      `/api/questionnaire/background?id=${id}`,
      { method: 'POST', body: form },
      token,
    )
  },

  removeBackground: (id: number, token: string) =>
    apiFetch<null>(
      `/api/questionnaire/background?id=${id}`,
      { method: 'DELETE' },
      token,
    ),

  remove: (id: number, token: string) =>
    apiFetch<null>(`/api/questionnaire/delete?id=${id}`, { method: 'DELETE' }, token),

  copy: (id: number, token: string) =>
    apiFetch<{ id: number }>('/api/questionnaire/copy', {
      method: 'POST',
      body: JSON.stringify({ id }),
    }, token),

  publish: (id: number, token: string) =>
    apiFetch<{
      id: number
      status?: string
      publicCode?: string
      publicUrl?: string
      qrCodeUrl?: string
      publishedAt?: string
    }>(
      '/api/questionnaire/publish',
      { method: 'POST', body: JSON.stringify({ id }) },
      token,
    ),

  close: (id: number, token: string) =>
    apiFetch<{ id: number }>('/api/questionnaire/close', {
      method: 'POST',
      body: JSON.stringify({ id }),
    }, token),
}

function serializeQuestionnaire(payload: Questionnaire) {
  return {
    title: payload.title.trim(),
    description: payload.description?.trim() || null,
    anonymous: Boolean(payload.anonymous),
    questions: payload.questions.map((question, index) => ({
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
