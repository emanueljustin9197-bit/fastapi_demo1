import { apiFetch, queryString } from './client'

export interface AnalysisOverview {
  responseCount?: number
  validResponseCount?: number
  averageDurationSeconds?: number
  completionRate?: number
}

export interface AnalysisTrendPoint {
  label: string
  count: number
  date?: string
}

export type AnalysisChannelSource = 'publicLink' | 'qrCode' | 'wechat'

export interface AnalysisChannel {
  source: AnalysisChannelSource
  label: string
  count: number
  percentage: number
}

export const analysisApi = {
  overview: (questionnaireId: number, token: string) =>
    apiFetch<AnalysisOverview>(
      `/api/analysis/overview${queryString({ questionnaireId })}`,
      {},
      token,
    ),

  questions: (questionnaireId: number, token: string) =>
    apiFetch<any[]>(
      `/api/analysis/questions${queryString({ questionnaireId })}`,
      {},
      token,
    ),

  trend: (questionnaireId: number, days: number, token: string) =>
    apiFetch<AnalysisTrendPoint[]>(
      `/api/analysis/trend${queryString({ questionnaireId, days })}`,
      {},
      token,
    ),

  channels: (questionnaireId: number, token: string) =>
    apiFetch<AnalysisChannel[]>(
      `/api/analysis/channels${queryString({ questionnaireId })}`,
      {},
      token,
    ),
}
