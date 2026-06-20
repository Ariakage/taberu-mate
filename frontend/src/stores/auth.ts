import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  getApiErrorMessage,
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
} from '@/services/auth'
import type { LoginPayload, RegisterPayload, UserPublic } from '@/services/auth'
import { clearAuthSession, getAccessToken } from '@/services/authSession'

const USER_STORAGE_KEY = 'taberu_mate_user'

function readStoredUser() {
  if (typeof window === 'undefined') {
    return null
  }

  const raw = window.localStorage.getItem(USER_STORAGE_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as UserPublic
  } catch {
    window.localStorage.removeItem(USER_STORAGE_KEY)
    return null
  }
}

function writeStoredUser(user: UserPublic | null) {
  if (typeof window === 'undefined') {
    return
  }

  if (user) {
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
    return
  }

  window.localStorage.removeItem(USER_STORAGE_KEY)
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserPublic | null>(readStoredUser())
  const loading = ref(false)
  const initialized = ref(false)
  const errorMessage = ref('')

  const isAuthenticated = computed(() => Boolean(user.value && getAccessToken()))
  const displayName = computed(() => user.value?.nickname || user.value?.username || '')

  function setUser(nextUser: UserPublic | null) {
    user.value = nextUser
    writeStoredUser(nextUser)
  }

  async function initialize() {
    if (initialized.value) {
      return
    }

    initialized.value = true

    if (!getAccessToken()) {
      setUser(null)
      return
    }

    try {
      setUser(await getCurrentUser())
    } catch {
      clearAuthSession()
      setUser(null)
    }
  }

  async function login(payload: LoginPayload) {
    loading.value = true
    errorMessage.value = ''

    try {
      const response = await loginUser(payload)
      setUser(response.user)
      return true
    } catch (error) {
      errorMessage.value = getApiErrorMessage(error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload) {
    loading.value = true
    errorMessage.value = ''

    try {
      await registerUser(payload)
      const response = await loginUser({
        username: payload.username,
        password: payload.password,
      })
      setUser(response.user)
      return true
    } catch (error) {
      errorMessage.value = getApiErrorMessage(error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    errorMessage.value = ''

    try {
      await logoutUser()
    } catch {
      // Local session should still be cleared if the server session already expired.
    } finally {
      clearAuthSession()
      setUser(null)
      loading.value = false
    }
  }

  return {
    user,
    loading,
    initialized,
    errorMessage,
    isAuthenticated,
    displayName,
    initialize,
    login,
    register,
    logout,
  }
})
