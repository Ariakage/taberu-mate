import type { AxiosError } from 'axios'

import apiClient from '@/services/http'
import type { MenuScanPrice } from '@/services/menuScan'

export interface OrderAssistantLineInput {
  id: string
  name_original?: string | null
  name_translated?: string | null
  quantity: number
  price?: MenuScanPrice | null
  tags?: string[]
}

export interface GenerateOrderMenuInput {
  restaurant_name_original?: string | null
  restaurant_name_translated?: string | null
  source_language?: string
  target_language?: string
  target_language_code?: string
  currency?: string
  customer_remark: string
  total_amount: number
  total_label: string
  items: OrderAssistantLineInput[]
}

export interface GeneratedOrderMenuItem {
  id: string
  name: string
  original_name: string | null
  quantity: number
  unit_price: {
    amount: number | null
    currency: string | null
    raw_text: string | null
  }
  subtotal: {
    amount: number | null
    currency: string | null
    display_text: string
  }
  item_note: string | null
}

export interface GeneratedOrderMenu {
  order: {
    title: string
    target_language: string
    currency: string | null
  }
  items: GeneratedOrderMenuItem[]
  customer_note: string | null
  restaurant_note: string
  local_language_order_text: string
  user_language_summary: string
  allergen_warnings: string[]
  total: {
    amount: number | null
    currency: string | null
    display_text: string
  }
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

const ORDER_MENU_SYSTEM_PROMPT = `
You generate a clear restaurant order sheet from selected menu items and a customer's free-form
remark. Return only JSON matching the provided schema. Keep quantities exact. Preserve original
dish names when present. Use the requested target_language for local_language_order_text and
restaurant_note. Use concise wording that can be shown directly to restaurant staff. Include allergy
warnings only when the customer_remark explicitly says the user has an allergy or asks staff to
confirm an allergy. Do not mention possible allergens just because a dish could contain them. Do
not add unrequested dishes. Respect dialect and locale variants such as Hong Kong Cantonese,
Taiwanese Hakka, English UK, English US, Japanese, Korean, and Thai when target_language asks for
them.
`.trim()

const ORDER_MENU_RESPONSE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: [
    'order',
    'items',
    'customer_note',
    'restaurant_note',
    'local_language_order_text',
    'user_language_summary',
    'allergen_warnings',
    'total',
  ],
  properties: {
    order: {
      type: 'object',
      additionalProperties: false,
      required: ['title', 'target_language', 'currency'],
      properties: {
        title: { type: 'string' },
        target_language: { type: 'string' },
        currency: { type: ['string', 'null'] },
      },
    },
    items: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'name', 'original_name', 'quantity', 'unit_price', 'subtotal', 'item_note'],
        properties: {
          id: { type: 'string' },
          name: { type: 'string' },
          original_name: { type: ['string', 'null'] },
          quantity: { type: 'integer' },
          unit_price: {
            type: 'object',
            additionalProperties: false,
            required: ['amount', 'currency', 'raw_text'],
            properties: {
              amount: { type: ['number', 'null'] },
              currency: { type: ['string', 'null'] },
              raw_text: { type: ['string', 'null'] },
            },
          },
          subtotal: {
            type: 'object',
            additionalProperties: false,
            required: ['amount', 'currency', 'display_text'],
            properties: {
              amount: { type: ['number', 'null'] },
              currency: { type: ['string', 'null'] },
              display_text: { type: 'string' },
            },
          },
          item_note: { type: ['string', 'null'] },
        },
      },
    },
    customer_note: { type: ['string', 'null'] },
    restaurant_note: { type: 'string' },
    local_language_order_text: { type: 'string' },
    user_language_summary: { type: 'string' },
    allergen_warnings: {
      type: 'array',
      items: { type: 'string' },
    },
    total: {
      type: 'object',
      additionalProperties: false,
      required: ['amount', 'currency', 'display_text'],
      properties: {
        amount: { type: ['number', 'null'] },
        currency: { type: ['string', 'null'] },
        display_text: { type: 'string' },
      },
    },
  },
}

export async function generateOrderMenu(input: GenerateOrderMenuInput) {
  const { data } = await apiClient.post<ChatCompletionResponse>(
    '/ai/chat',
    {
      prompt: ORDER_MENU_SYSTEM_PROMPT,
      message: JSON.stringify(input),
      response_format: 'json_schema',
      json_schema: {
        name: 'generated_order_menu',
        strict: true,
        schema: ORDER_MENU_RESPONSE_SCHEMA,
      },
      max_completion_tokens: 2500,
    },
    {
      timeout: 120_000,
    },
  )

  if (data.error) {
    const code = data.error.code ? ` (${data.error.code})` : ''
    throw new Error(`${data.error.message || 'AI 点菜单生成失败'}${code}`)
  }

  const content = data.choices?.[0]?.message?.content
  if (!content) {
    throw new Error('AI 点菜单结果为空')
  }

  return parseOrderMenuContent(content)
}

export function getOrderAssistantErrorMessage(error: unknown) {
  const axiosError = error as AxiosError<{ detail?: string }>
  const detail = axiosError.response?.data?.detail

  if (detail) {
    return detail
  }

  if (axiosError.response?.status === 401) {
    return '需要登录后才能生成点菜单'
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return 'AI 点菜单生成失败，请稍后再试'
}

function parseOrderMenuContent(content: string) {
  const normalized = content
    .trim()
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim()

  return JSON.parse(normalized) as GeneratedOrderMenu
}
