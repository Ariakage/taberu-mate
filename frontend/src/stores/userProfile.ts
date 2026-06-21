import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createOrderHistory,
  getUserDashboard,
  getUserProfileErrorMessage,
  updateUserProfile,
} from '@/services/userProfile'
import type {
  OrderHistoryCreate,
  OrderHistoryEntry,
  UserDashboard,
  UserProfile,
  UserProfileUpdate,
} from '@/services/userProfile'

export const useUserProfileStore = defineStore('userProfile', () => {
  const dashboard = ref<UserDashboard | null>(null)
  const profile = ref<UserProfile | null>(null)
  const recentOrders = ref<OrderHistoryEntry[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const errorMessage = ref('')

  const stats = computed(
    () =>
      dashboard.value?.stats ?? {
        avoid_count: profile.value?.avoidances.length ?? 0,
        allergy_count: profile.value?.allergies.length ?? 0,
        order_count: recentOrders.value.length,
        updated_at: profile.value?.updated_at ?? recentOrders.value[0]?.created_at ?? null,
      },
  )

  function applyDashboard(nextDashboard: UserDashboard) {
    dashboard.value = nextDashboard
    profile.value = nextDashboard.profile
    recentOrders.value = nextDashboard.recent_orders
  }

  async function loadDashboard(force = false) {
    if (loading.value || (dashboard.value && !force)) {
      return dashboard.value
    }

    loading.value = true
    errorMessage.value = ''

    try {
      const nextDashboard = await getUserDashboard()
      applyDashboard(nextDashboard)
      return nextDashboard
    } catch (error) {
      errorMessage.value = getUserProfileErrorMessage(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function saveProfile(payload: UserProfileUpdate) {
    saving.value = true
    errorMessage.value = ''

    try {
      profile.value = await updateUserProfile(payload)
      if (dashboard.value) {
        dashboard.value = {
          ...dashboard.value,
          profile: profile.value,
          stats: {
            ...dashboard.value.stats,
            avoid_count: profile.value.avoidances.length,
            allergy_count: profile.value.allergies.length,
            updated_at: profile.value.updated_at,
          },
        }
      }
      return profile.value
    } catch (error) {
      errorMessage.value = getUserProfileErrorMessage(error)
      throw error
    } finally {
      saving.value = false
    }
  }

  async function saveOrderHistory(payload: OrderHistoryCreate) {
    saving.value = true
    errorMessage.value = ''

    try {
      const order = await createOrderHistory(payload)
      recentOrders.value = [order, ...recentOrders.value].slice(0, 5)
      if (dashboard.value) {
        dashboard.value = {
          ...dashboard.value,
          recent_orders: recentOrders.value,
          stats: {
            ...dashboard.value.stats,
            order_count: dashboard.value.stats.order_count + 1,
            updated_at: order.created_at,
          },
        }
      }
      return order
    } catch (error) {
      errorMessage.value = getUserProfileErrorMessage(error)
      throw error
    } finally {
      saving.value = false
    }
  }

  function clear() {
    dashboard.value = null
    profile.value = null
    recentOrders.value = []
    errorMessage.value = ''
  }

  return {
    dashboard,
    profile,
    recentOrders,
    stats,
    loading,
    saving,
    errorMessage,
    loadDashboard,
    saveProfile,
    saveOrderHistory,
    clear,
  }
})
