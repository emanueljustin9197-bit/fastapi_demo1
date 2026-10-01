export type QuestionType = 'single' | 'multiple' | 'text' | 'date' | 'rating' | 'number' | 'phone'

export interface OptionItem {
  id?: number
  label: string
  sortOrder: number
}

export interface QuestionItem {
  id?: number
  type: QuestionType
  title: string
  required: boolean
  sortOrder: number
  options: OptionItem[]
}

export interface Questionnaire {
  id?: number
  title: string
  description?: string | null
  status?: 'draft' | 'active' | 'closed' | string
  anonymous: boolean
  oneResponse?: boolean
  showResult?: boolean
  publicCode?: string | null
  publicUrl?: string | null
  backgroundImage?: string | null
  publishedAt?: string | null
  closedAt?: string | null
  questions: QuestionItem[]
  questionCount?: number
  responseCount?: number
  completionRate?: number
  createdAt?: string
  updatedAt?: string
}

export interface UserInfo {
  id?: number
  name?: string | null
  email?: string | null
  phone?: string | null
  company?: string | null
  avatar?: string | null
}

export interface AnswerPayload {
  questionId: number
  optionIds: number[]
  content?: string | null
}
