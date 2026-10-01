import { apiFetch } from './client'
import type { AnswerPayload, Questionnaire } from '../types'

export type ResponseSource = 'publicLink' | 'qrCode' | 'wechat'

export interface PublicResponsePayload {
  publicCode: string
  source: ResponseSource
  durationSeconds: number
  respondentName: string | null
  respondentEmail: string | null
  answers: AnswerPayload[]
}

export const publicApi = {
  questionnaire: (publicCode: string) =>
    apiFetch<Questionnaire>(
      `/api/public/questionnaire?publicCode=${encodeURIComponent(publicCode)}`,
    ),

  submitResponse: (payload: PublicResponsePayload) =>
    apiFetch<{ id: number }>('/api/public/response/submit', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
