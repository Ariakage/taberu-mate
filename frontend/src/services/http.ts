import axios from 'axios'
import type { AxiosError } from 'axios'

import {
  clearAuthSession,
  getAccessToken,
  getCsrfToken,
  setAccessToken,
  setCsrfToken,
} from '@/services/authSession'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL,
  timeout: 10_000,
  withCredentials: true,
})

const refreshClient = axios.create({
  baseURL,
  timeout: 10_000,
  withCredentials: true,
})

let refreshPromise: Promise<string | null> | null = null

async function fetchCsrfToken() {
  const { data } = await refreshClient.get<{ csrf_token: string }>('/auth/csrf')
  setCsrfToken(data.csrf_token)
  return data.csrf_token
}

async function refreshAccessToken() {
  refreshPromise ??= (async () => {
    try {
      const csrfToken = getCsrfToken() || (await fetchCsrfToken())
      const { data } = await refreshClient.post<{
        access_token: string
        csrf_token: string
      }>(
        '/auth/refresh',
        undefined,
        {
          headers: {
            'X-CSRF-Token': csrfToken,
          },
        },
      )

      setAccessToken(data.access_token)
      setCsrfToken(data.csrf_token)
      return data.access_token
    } catch {
      clearAuthSession()
      return null
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

apiClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  const csrfToken = getCsrfToken()
  const method = config.method?.toLowerCase()

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  if (csrfToken && method && !['get', 'head', 'options'].includes(method)) {
    config.headers['X-CSRF-Token'] = csrfToken
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !('retryAfterRefresh' in originalRequest)
    ) {
      Object.assign(originalRequest, { retryAfterRefresh: true })

      const accessToken = await refreshAccessToken()
      if (accessToken) {
        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return apiClient(originalRequest)
      }
    }

    return Promise.reject(error)
  },
)

export default apiClient
