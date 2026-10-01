import { apiFetch } from './client'
import type { UserInfo } from '../types'

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<{ token: string }>('/api/user/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (name: string, email: string, password: string) =>
    apiFetch<{ token: string }>('/api/user/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  info: (token: string) => apiFetch<UserInfo>('/api/user/info', {}, token),

  update: (payload: Partial<UserInfo>, token: string) =>
    apiFetch<UserInfo>('/api/user/update', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }, token),

  uploadAvatar: (file: File, token: string) => {
    const form = new FormData()
    form.append('file', file)
    return apiFetch<UserInfo>('/api/user/avatar', {
      method: 'POST',
      body: form,
    }, token)
  },
}
