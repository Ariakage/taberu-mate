import type { AxiosError } from 'axios'

import apiClient from '@/services/http'
import { setAccessToken, setCsrfToken } from '@/services/authSession'

export interface UserPublic {
  id: string
  username: string
  nickname: string
  avatar_url: string | null
  created_at: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload extends LoginPayload {
  nickname?: string
  avatar_url?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_expires_in: number
  csrf_token: string
  user: UserPublic
}

export async function issueCsrfToken() {
  const { data } = await apiClient.get<{ csrf_token: string }>('/auth/csrf')
  setCsrfToken(data.csrf_token)
  return data.csrf_token
}

async function ensureCsrfToken() {
  return issueCsrfToken()
}

export async function registerUser(payload: RegisterPayload) {
  await ensureCsrfToken()

  const { data } = await apiClient.post<UserPublic>('/auth/register', {
    username: payload.username,
    nickname: payload.nickname || undefined,
    avatar_url: payload.avatar_url || undefined,
    password: payload.password,
  })

  return data
}

export async function loginUser(payload: LoginPayload) {
  await ensureCsrfToken()

  const { data } = await apiClient.post<TokenResponse>('/auth/login', payload)
  setAccessToken(data.access_token)
  setCsrfToken(data.csrf_token)
  return data
}

export async function getCurrentUser() {
  const { data } = await apiClient.get<UserPublic>('/users/me')
  return data
}

export async function logoutUser() {
  await ensureCsrfToken()
  await apiClient.post('/auth/logout')
}

export function getApiErrorMessage(error: unknown) {
  const axiosError = error as AxiosError<{ detail?: string }>
  const detail = axiosError.response?.data?.detail

  if (detail) {
    return detail
  }

  if (axiosError.response?.status === 401) {
    return '用户名或密码不正确'
  }

  if (axiosError.response?.status === 409) {
    return '用户名已存在'
  }

  if (axiosError.response?.status === 429) {
    return '尝试次数太多，请稍后再试'
  }

  return '请求失败，请稍后再试'
}
