export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
export const AUTH_EXPIRED_EVENT = 'survey-auth-expired'

function expireSession() {
  localStorage.removeItem('survey_token')
  localStorage.removeItem('survey_user')
  window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT, {
    detail: { message: '登录已失效，请重新登录' },
  }))
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers })
  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    if (response.status === 401 && token) {
      expireSession()
      throw new Error('登录已失效，请重新登录')
    }

    const detail = typeof body === 'object' && body
      ? body.detail || body.message
      : body
    throw new Error(detail || `请求失败（${response.status}）`)
  }

  if (typeof body === 'object' && body && 'data' in body) {
    return body.data as T
  }
  return body as T
}

export function assetUrl(path?: string | null): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path) || path.startsWith('data:')) return path
  return `${apiBaseUrl}${path}`
}

export function queryString(params: Record<string, unknown>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value))
    }
  }
  const result = query.toString()
  return result ? `?${result}` : ''
}
