import type { AxiosError } from 'axios'

import apiClient from '@/services/http'

export interface UserProfile {
  user_id: string
  avoidances: string[]
  allergies: string[]
  notes: string
  updated_at: string | null
}

export interface UserProfileUpdate {
  avoidances: string[]
  allergies: string[]
  notes: string
}

export interface OrderHistoryEntry {
  id: string
  user_id: string
  restaurant_name: string | null
  target_language: string | null
  customer_remark: string
  total_label: string
  total_amount: number | null
  items: Array<Record<string, unknown>>
  generated_order: Record<string, unknown> | null
  created_at: string
}

export interface OrderHistoryCreate {
  restaurant_name?: string | null
  target_language?: string | null
  customer_remark: string
  total_label: string
  total_amount?: number | null
  items: Array<Record<string, unknown>>
  generated_order?: Record<string, unknown> | null
}

export interface UserDashboard {
  profile: UserProfile
  recent_orders: OrderHistoryEntry[]
  stats: {
    avoid_count: number
    allergy_count: number
    order_count: number
    updated_at: string | null
  }
}

export async function getUserProfile() {
  const { data } = await apiClient.get<UserProfile>('/users/me/profile')
  return data
}

export async function updateUserProfile(payload: UserProfileUpdate) {
  const { data } = await apiClient.put<UserProfile>('/users/me/profile', payload)
  return data
}

export async function listOrderHistory(limit = 20) {
  const { data } = await apiClient.get<OrderHistoryEntry[]>('/users/me/orders', {
    params: { limit },
  })
  return data
}

export async function createOrderHistory(payload: OrderHistoryCreate) {
  const { data } = await apiClient.post<OrderHistoryEntry>('/users/me/orders', payload)
  return data
}

export async function getUserDashboard() {
  const { data } = await apiClient.get<UserDashboard>('/users/me/dashboard')
  return data
}

export function getUserProfileErrorMessage(error: unknown) {
  const axiosError = error as AxiosError<{ detail?: string }>
  const detail = axiosError.response?.data?.detail

  if (detail) {
    return detail
  }

  if (axiosError.response?.status === 401) {
    return '需要登录后才能同步饭饭档案'
  }

  if (axiosError.response?.status === 403) {
    return '登录状态已过期，请重新登录'
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return '饭饭档案同步失败，请稍后再试'
}
