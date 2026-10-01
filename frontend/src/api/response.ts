import { apiFetch, queryString } from './client'

export interface ResponseSummary {
  id: number
  source: string
  durationSeconds: number
  isValid: boolean
  submittedAt: string
  respondentName?: string | null
  respondentEmail?: string | null
}

export interface ResponseDetail extends ResponseSummary {
  questionnaireId: number
  answers: Array<{
    questionId: number
    questionTitle?: string
    optionIds: number[]
    optionLabels: string[]
    content?: string | null
  }>
}

export const responseApi = {
  list: (questionnaireId: number, token: string, page = 1, pageSize = 50) =>
    apiFetch<{ list: ResponseSummary[]; total: number }>(
      `/api/response/list${queryString({ questionnaireId, page, pageSize })}`,
      {},
      token,
    ),

  detail: (id: number, token: string) =>
    apiFetch<ResponseDetail>(`/api/response/detail?id=${id}`, {}, token),
}
