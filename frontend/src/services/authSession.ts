const ACCESS_TOKEN_KEY = 'taberu_mate_access_token'
const CSRF_TOKEN_KEY = 'taberu_mate_csrf_token'

function readStorage(key: string) {
  if (typeof window === 'undefined') {
    return ''
  }

  return window.localStorage.getItem(key) ?? ''
}

function writeStorage(key: string, value: string) {
  if (typeof window === 'undefined') {
    return
  }

  if (value) {
    window.localStorage.setItem(key, value)
    return
  }

  window.localStorage.removeItem(key)
}

export function getAccessToken() {
  return readStorage(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token: string) {
  writeStorage(ACCESS_TOKEN_KEY, token)
}

export function getCsrfToken() {
  return readStorage(CSRF_TOKEN_KEY)
}

export function setCsrfToken(token: string) {
  writeStorage(CSRF_TOKEN_KEY, token)
}

export function clearAuthSession() {
  writeStorage(ACCESS_TOKEN_KEY, '')
  writeStorage(CSRF_TOKEN_KEY, '')
}
