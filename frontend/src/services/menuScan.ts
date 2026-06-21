import type { AxiosError } from 'axios'

import { getAccessToken, getCsrfToken } from '@/services/authSession'

export interface MenuScanMenu {
  source_language?: string
  target_language?: string
  currency?: string
  restaurant_name_original?: string | null
  restaurant_name_translated?: string | null
}

export interface MenuScanCategory {
  id: string
  parent_id?: string | null
  name_original?: string | null
  name_translated?: string | null
  type?: string | null
  sort_order?: number | null
}

export interface MenuScanPrice {
  amount?: number | null
  currency?: string | null
  raw_text?: string | null
}

export interface MenuScanConfidence {
  ocr?: number | null
  translation?: number | null
  classification?: number | null
  price_detection?: number | null
  allergen_detection?: number | null
}

export interface MenuScanAvailability {
  status?: string | null
  note?: string | null
}

export interface MenuScanDietary {
  contains_alcohol?: boolean | null
  contains_beef?: boolean | null
  contains_chicken?: boolean | null
  contains_pork?: boolean | null
  contains_seafood?: boolean | null
  halal?: boolean | null
  vegan?: boolean | null
  vegetarian?: boolean | null
}

export interface MenuScanTasteProfile {
  bitter_level?: number | null
  richness_level?: number | null
  salty_level?: number | null
  sour_level?: number | null
  spicy_level?: number | null
  sweet_level?: number | null
}

export interface MenuScanItem {
  id: string
  primary_category_id?: string | null
  category_ids?: string[]
  name_original?: string | null
  name_translated?: string | null
  description_original?: string | null
  description_translated?: string | null
  price?: MenuScanPrice | null
  item_type?: string | null
  tags?: string[]
  allergens?: string[]
  dietary?: MenuScanDietary | null
  taste_profile?: MenuScanTasteProfile | null
  availability?: MenuScanAvailability | null
  confidence?: MenuScanConfidence | null
}

export interface MenuScanResult {
  menu: MenuScanMenu
  categories: MenuScanCategory[]
  items: MenuScanItem[]
}

interface ChatCompletionResponse {
  choices?: Array<{
    message?: {
      content?: string | null
    }
  }> | null
  error?: {
    message?: string
    code?: string
  } | null
}

interface MenuScanStreamEvent {
  event: string
  data: {
    content?: string
    message?: string
  }
}

function parseMenuContent(content: string) {
  const normalized = content
    .trim()
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim()

  return JSON.parse(normalized) as MenuScanResult
}

export async function scanMenuImage(
  image: File,
  targetLanguage = '简体中文',
  onUploadProgress?: (progress: number | null) => void,
  onStatus?: (message: string) => void,
) {
  const formData = new FormData()
  formData.append('target_language', targetLanguage)
  formData.append('image', image)

  console.info('[menu-scan] request starting', {
    fileName: image.name,
    fileSize: image.size,
    fileType: image.type,
    targetLanguage,
  })

  const data = await postMenuScanStream(formData, onUploadProgress, onStatus)
  console.info('[menu-scan] stream completed')

  if (data.error) {
    const code = data.error.code ? ` (${data.error.code})` : ''
    throw new Error(`${data.error.message || '菜单识别服务返回错误'}${code}`)
  }

  const content = data.choices?.[0]?.message?.content

  if (!content) {
    throw new Error('菜单识别结果为空')
  }

  return parseMenuContent(content)
}

async function postMenuScanStream(
  formData: FormData,
  onUploadProgress?: (progress: number | null) => void,
  onStatus?: (message: string) => void,
): Promise<ChatCompletionResponse> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 600_000)
  console.info('[menu-scan] stream fetch starting', {
    url: apiUrl('/menus/scan/stream'),
  })
  const response = await fetch(apiUrl('/menus/scan/stream'), {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
    credentials: 'include',
    signal: controller.signal,
  }).finally(() => window.clearTimeout(timeoutId))

  console.info('[menu-scan] stream response opened', {
    ok: response.ok,
    status: response.status,
    contentType: response.headers.get('content-type'),
  })

  if (!response.ok) {
    throw new Error(await readErrorResponse(response))
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式菜单识别响应')
  }

  onUploadProgress?.(100)
  onStatus?.('图片已上传，正在等待模型返回...')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let streamedContent = ''
  let doneContent = ''

  while (true) {
    const { done, value } = await reader.read()

    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    buffer = buffer.replace(/\r\n/g, '\n')

    let separatorIndex = buffer.indexOf('\n\n')
    while (separatorIndex >= 0) {
      const rawEvent = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)
      const parsedEvent = parseStreamEvent(rawEvent)

      if (parsedEvent?.event === 'status' && parsedEvent.data.message) {
        console.info('[menu-scan] status', parsedEvent.data.message)
        onStatus?.(parsedEvent.data.message)
      }

      if (parsedEvent?.event === 'delta' && parsedEvent.data.content) {
        streamedContent += parsedEvent.data.content
        console.debug('[menu-scan] delta', {
          deltaChars: parsedEvent.data.content.length,
          totalChars: streamedContent.length,
        })
        onStatus?.(`正在接收识别结果... ${streamedContent.length} 字符`)
      }

      if (parsedEvent?.event === 'done') {
        doneContent = parsedEvent.data.content || streamedContent
        console.info('[menu-scan] done', {
          contentChars: doneContent.length,
        })
        onStatus?.('菜单识别完成，正在解析结果...')
      }

      if (parsedEvent?.event === 'error') {
        console.error('[menu-scan] stream error event', parsedEvent.data)
        throw new Error(parsedEvent.data.message || '菜单识别服务返回错误')
      }

      separatorIndex = buffer.indexOf('\n\n')
    }
  }

  const content = doneContent || streamedContent
  if (!content) {
    throw new Error('菜单识别结果为空')
  }

  const completion: ChatCompletionResponse = {
    choices: [{ message: { content } }],
  }
  return completion
}

function apiUrl(path: string) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || ''
  return `${baseURL.replace(/\/$/, '')}${path}`
}

function authHeaders() {
  const headers = new Headers()
  const accessToken = getAccessToken()
  const csrfToken = getCsrfToken()

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  if (csrfToken) {
    headers.set('X-CSRF-Token', csrfToken)
  }

  return headers
}

async function readErrorResponse(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string }
    return body.detail || `菜单识别请求失败：${response.status}`
  } catch {
    return `菜单识别请求失败：${response.status}`
  }
}

function parseStreamEvent(rawEvent: string): MenuScanStreamEvent | null {
  const lines = rawEvent.split('\n')
  const eventLine = lines.find((line) => line.startsWith('event:'))
  const dataLines = lines
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice('data:'.length).trimStart())

  if (!eventLine || !dataLines.length) {
    return null
  }

  try {
    return {
      event: eventLine.slice('event:'.length).trim(),
      data: JSON.parse(dataLines.join('\n')) as MenuScanStreamEvent['data'],
    }
  } catch {
    return null
  }
}

export function getMenuScanErrorMessage(error: unknown) {
  const axiosError = error as AxiosError<{ detail?: string }>
  const detail = axiosError.response?.data?.detail

  console.error('[menu-scan] request failed', {
    code: axiosError.code,
    status: axiosError.response?.status,
    detail,
    message: error instanceof Error ? error.message : String(error),
  })

  if (detail) {
    return detail
  }

  if (axiosError.code === 'ECONNABORTED') {
    return '菜单识别超时，请换一张更清晰的图片或稍后再试'
  }

  if (axiosError.response?.status === 400) {
    return '图片无法识别，请换一张清晰的菜单照片'
  }

  if (axiosError.response?.status === 401) {
    return '需要登录才能使用菜单识别'
  }

  if (axiosError.response?.status === 502) {
    return '菜单识别服务暂时失败，请稍后再试'
  }

  if (axiosError.response?.status === 503) {
    return '后端还没有配置菜单识别服务'
  }

  if (error instanceof Error) {
    return error.message
  }

  return '菜单识别失败，请稍后再试'
}
