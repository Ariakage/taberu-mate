<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { ClipboardList, Home, UserRound } from 'lucide-vue-next'
import { Tabbar as VanTabbar, TabbarItem as VanTabbarItem } from 'vant'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const tabs = [
  {
    name: 'home',
    label: '首页',
    path: '/',
    icon: Home,
  },
  {
    name: 'orders',
    label: '点单',
    path: '/orders',
    icon: ClipboardList,
  },
  {
    name: 'profile',
    label: '我的',
    path: '/profile',
    icon: UserRound,
  },
]

const activeTab = computed({
  get: () => String(route.meta.tab ?? 'home'),
  set: (name: string) => {
    const target = tabs.find((tab) => tab.name === name)

    if (target && target.path !== route.path) {
      void router.push(target.path)
    }
  },
})

onMounted(() => {
  void authStore.initialize()
})
</script>

<template>
  <div class="min-h-dvh bg-[#FFF8EF] text-[#1F2937]">
    <main class="tm-app-bg mx-auto min-h-dvh w-full max-w-[430px] border-x border-[#EFDCCC]">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <VanTabbar v-model="activeTab" class="taberu-tabbar">
      <VanTabbarItem v-for="tab in tabs" :key="tab.name" :name="tab.name">
        <template #icon="{ active }">
          <component :is="tab.icon" :size="20" :stroke-width="active ? 2.7 : 2.1" />
        </template>
        {{ tab.label }}
      </VanTabbarItem>
    </VanTabbar>
  </div>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

:global(.taberu-tabbar) {
  right: auto !important;
  left: 50% !important;
  bottom: calc(12px + env(safe-area-inset-bottom)) !important;
  width: calc(100% - 72px);
  max-width: 320px;
  height: 56px;
  padding: 4px;
  transform: translateX(-50%);
  border: 1px solid rgba(239, 220, 204, 0.92);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(18px) saturate(1.35);
  -webkit-backdrop-filter: blur(18px) saturate(1.35);
}

:global(.taberu-tabbar .van-tabbar-item) {
  height: 48px;
  flex: 1 1 0;
  border-radius: 16px;
  color: #667085;
  font-weight: 700;
  line-height: 1;
  transition:
    background 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

:global(.taberu-tabbar .van-tabbar-item__icon) {
  margin-bottom: 2px;
}

:global(.taberu-tabbar .van-tabbar-item__text) {
  line-height: 1.1;
}

:global(.taberu-tabbar .van-tabbar-item--active) {
  color: #ff7a45;
  background: rgba(255, 122, 69, 0.12);
  box-shadow:
    inset 0 0 0 1px rgba(255, 122, 69, 0.22),
    0 6px 18px rgba(255, 122, 69, 0.14);
  transform: translateY(-1px);
}

:global(.taberu-tabbar::after) {
  display: none;
}
</style>
