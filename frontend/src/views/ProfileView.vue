<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import {
  CalendarClock,
  ClipboardList,
  CloudSync,
  History,
  ListChecks,
  LogOut,
  UserRound,
} from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { displayName, errorMessage, isAuthenticated, loading, user } = storeToRefs(authStore)
const mode = ref<'login' | 'register'>('login')

const form = reactive({
  username: '',
  nickname: '',
  avatarUrl: '',
  password: '',
})

const modeTitle = computed(() => (mode.value === 'login' ? '欢迎回来' : '创建账号'))
const submitText = computed(() => (mode.value === 'login' ? '登录' : '注册并登录'))
const switchText = computed(() => (mode.value === 'login' ? '还没有账号？创建一个' : '已有账号？去登录'))
const loginOverviewTitle = computed(() => (isAuthenticated.value && user.value ? '已登录到食べ友账号' : '登录后开启饭饭档案'))
const loginOverviewText = computed(() =>
  isAuthenticated.value && user.value
    ? `当前账号 @${user.value.username}，忌口、过敏和历史菜单会保存到这个档案。`
    : '登录或创建账号后，忌口、过敏和常用备注才会保存到你的档案。',
)
const savedProfileText = computed(() =>
  isAuthenticated.value ? '当前账号可继续补充忌口和过敏信息' : '登录后保存忌口、过敏和常用备注',
)
const sessionHintText = computed(() =>
  isAuthenticated.value ? '退出登录前，饭饭档案会留在账号里' : '使用账号登录，换设备也能找回档案',
)
const profileStats = computed(() => ({
  avoidCount: isAuthenticated.value ? '3 条' : '登录后同步',
  allergyCount: isAuthenticated.value ? '2 条' : '登录后同步',
  menuCount: isAuthenticated.value ? '6 份' : '登录后同步',
  updatedAt: isAuthenticated.value ? '今天 18:20' : '尚未同步',
}))

function switchMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  authStore.errorMessage = ''
}

async function submitAuth() {
  if (mode.value === 'login') {
    await authStore.login({
      username: form.username,
      password: form.password,
    })
    return
  }

  await authStore.register({
    username: form.username,
    nickname: form.nickname,
    avatar_url: form.avatarUrl,
    password: form.password,
  })
}
</script>

<template>
  <section class="min-h-dvh bg-transparent px-4 pb-32 text-[#1F2937] pt-[calc(env(safe-area-inset-top)+1rem)]">
    <header class="tm-card mb-4 p-4">
      <p class="text-sm font-semibold text-[#FF7A45]">食べ友</p>
      <h1 class="mt-2 text-2xl font-black leading-tight tracking-normal">我的饭饭档案</h1>
    </header>

    <section class="mb-4 grid gap-3">
      <article class="tm-card p-4">
        <div class="flex items-start gap-3">
          <div class="tm-icon-tile bg-[#FFF1E8] text-[#FF7A45]">
            <UserRound :size="21" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-black leading-5 text-[#1F2937]">{{ loginOverviewTitle }}</p>
            <p class="mt-1 text-xs font-semibold leading-5 text-[#667085]">
              {{ loginOverviewText }}
            </p>
          </div>
        </div>
      </article>

      <div class="grid grid-cols-2 gap-3">
        <article class="tm-card p-3">
          <ClipboardList class="mb-2 text-[#6BAF92]" :size="19" />
          <p class="text-xs font-black leading-4 text-[#1F2937]">档案保存</p>
          <p class="mt-1 text-[11px] font-semibold leading-4 text-[#667085]">{{ savedProfileText }}</p>
        </article>
        <article class="tm-card p-3">
          <History class="mb-2 text-[#8ABFE8]" :size="19" />
          <p class="text-xs font-black leading-4 text-[#1F2937]">登录会话</p>
          <p class="mt-1 text-[11px] font-semibold leading-4 text-[#667085]">{{ sessionHintText }}</p>
        </article>
      </div>
    </section>

    <section v-if="isAuthenticated && user" class="tm-card p-4">
      <div class="flex items-start gap-3">
        <img
          v-if="user.avatar_url"
          class="size-14 rounded-lg border border-[#EFDCCC] object-cover"
          :src="user.avatar_url"
          :alt="displayName"
        />
        <div v-else class="grid size-14 place-items-center rounded-lg bg-[#FFF1E8] text-[#FF7A45]">
          <UserRound :size="28" />
        </div>

        <div class="min-w-0 flex-1">
          <p class="truncate text-xl font-black leading-6">{{ displayName }}</p>
          <p class="mt-1 truncate text-sm font-semibold text-[#667085]">@{{ user.username }}</p>
          <p class="mt-2 text-xs font-semibold text-[#667085]">食べ友会帮你记住忌口、过敏和常用备注。</p>
        </div>
      </div>

      <div class="mt-5 grid grid-cols-3 gap-2">
        <div class="tm-card-muted p-3">
          <ListChecks class="mb-2 text-[#6BAF92]" :size="18" />
          <p class="text-xs font-black leading-4 text-[#1F2937]">忌口备注</p>
          <p class="mt-1 text-[11px] font-semibold leading-4 text-[#667085]">不吃香菜等</p>
        </div>
        <div class="tm-card-muted p-3">
          <ClipboardList class="mb-2 text-[#FF7A45]" :size="18" />
          <p class="text-xs font-black leading-4 text-[#1F2937]">过敏信息</p>
          <p class="mt-1 text-[11px] font-semibold leading-4 text-[#667085]">花生海鲜等</p>
        </div>
        <div class="tm-card-muted p-3">
          <History class="mb-2 text-[#8ABFE8]" :size="18" />
          <p class="text-xs font-black leading-4 text-[#1F2937]">历史菜单</p>
          <p class="mt-1 text-[11px] font-semibold leading-4 text-[#667085]">最近点过的</p>
        </div>
      </div>

      <button
        class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-[#FFD8D3] bg-[#FFF2F0] px-4 py-3 text-sm font-black text-[#B95048]"
        type="button"
        :disabled="loading"
        @click="authStore.logout"
      >
        <LogOut :size="17" />
        退出登录
      </button>
    </section>

    <section v-else class="tm-card overflow-hidden">
      <div class="border-b border-[#F3E3D6] p-4">
        <p class="text-sm font-semibold text-[#FF7A45]">{{ modeTitle }}</p>
        <h2 class="mt-2 text-2xl font-black leading-tight tracking-normal">
          记录忌口、过敏和常用备注，旅行点餐时一键带上。
        </h2>
        <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
          你的偏好会被安全保存，只在点餐辅助时使用。
        </p>
      </div>

      <form class="space-y-3 p-4" @submit.prevent="submitAuth">
        <label class="block">
          <span class="text-xs font-black text-[#667085]">用户名</span>
          <input
            v-model.trim="form.username"
            class="mt-1 w-full rounded-lg border border-[#EFDCCC] bg-white px-3 py-3 text-sm font-semibold outline-none focus:border-[#FF7A45]"
            autocomplete="username"
            maxlength="32"
            minlength="3"
            placeholder="用户名"
            required
          />
        </label>

        <label v-if="mode === 'register'" class="block">
          <span class="text-xs font-black text-[#667085]">昵称</span>
          <input
            v-model.trim="form.nickname"
            class="mt-1 w-full rounded-lg border border-[#EFDCCC] bg-white px-3 py-3 text-sm font-semibold outline-none focus:border-[#FF7A45]"
            maxlength="50"
            placeholder="不填则默认使用用户名"
          />
        </label>

        <label v-if="mode === 'register'" class="block">
          <span class="text-xs font-black text-[#667085]">头像 URL</span>
          <input
            v-model.trim="form.avatarUrl"
            class="mt-1 w-full rounded-lg border border-[#EFDCCC] bg-white px-3 py-3 text-sm font-semibold outline-none focus:border-[#FF7A45]"
            inputmode="url"
            placeholder="https://example.com/avatar.png"
          />
        </label>

        <label class="block">
          <span class="text-xs font-black text-[#667085]">密码</span>
          <input
            v-model="form.password"
            class="mt-1 w-full rounded-lg border border-[#EFDCCC] bg-white px-3 py-3 text-sm font-semibold outline-none focus:border-[#FF7A45]"
            autocomplete="current-password"
            maxlength="128"
            minlength="8"
            placeholder="至少 8 位"
            required
            type="password"
          />
        </label>

        <p
          v-if="errorMessage"
          class="rounded-lg border border-[#FFD8D3] bg-[#FFF2F0] px-3 py-2 text-xs font-black text-[#B95048]"
        >
          {{ errorMessage }}
        </p>

        <button
          class="w-full rounded-lg border border-[#FFC8A8] bg-[#FF7A45] px-4 py-3 text-sm font-black text-white disabled:opacity-60"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? '处理中...' : submitText }}
        </button>

        <button
          class="w-full rounded-lg border border-[#EFDCCC] bg-white px-4 py-3 text-sm font-black text-[#1F2937]"
          type="button"
          :disabled="loading"
          @click="switchMode"
        >
          {{ switchText }}
        </button>
      </form>
    </section>

    <section class="mt-4 tm-card overflow-hidden">
      <div class="border-b border-[#F3E3D6] p-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm font-black leading-5 text-[#1F2937]">饭饭档案概览</p>
            <p class="mt-1 text-xs font-semibold leading-5 text-[#667085]">
              这里先展示前端占位数据，之后可以从后端读取账号档案。
            </p>
          </div>
          <div class="tm-icon-tile bg-[#FFF1E8] text-[#FF7A45]">
            <CloudSync :size="21" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-2 p-4">
        <article class="tm-card-muted p-3">
          <ListChecks class="mb-2 text-[#6BAF92]" :size="18" />
          <p class="text-[11px] font-black leading-4 text-[#667085]">已保存忌口</p>
          <p class="mt-1 text-lg font-black leading-6 text-[#1F2937]">{{ profileStats.avoidCount }}</p>
        </article>
        <article class="tm-card-muted p-3">
          <ClipboardList class="mb-2 text-[#FF7A45]" :size="18" />
          <p class="text-[11px] font-black leading-4 text-[#667085]">过敏提醒</p>
          <p class="mt-1 text-lg font-black leading-6 text-[#1F2937]">{{ profileStats.allergyCount }}</p>
        </article>
        <article class="tm-card-muted p-3">
          <History class="mb-2 text-[#8ABFE8]" :size="18" />
          <p class="text-[11px] font-black leading-4 text-[#667085]">历史菜单</p>
          <p class="mt-1 text-lg font-black leading-6 text-[#1F2937]">{{ profileStats.menuCount }}</p>
        </article>
        <article class="tm-card-muted p-3">
          <CalendarClock class="mb-2 text-[#B95048]" :size="18" />
          <p class="text-[11px] font-black leading-4 text-[#667085]">上次同步</p>
          <p class="mt-1 text-sm font-black leading-6 text-[#1F2937]">{{ profileStats.updatedAt }}</p>
        </article>
      </div>

      <div class="px-4 pb-4">
        <div class="rounded-lg border border-[#DCECF8] bg-white p-3">
          <p class="text-xs font-black text-[#667085]">下一步建议</p>
          <p class="mt-1 text-sm font-semibold leading-5 text-[#1F2937]">
            优先补全过敏信息和常用忌口，之后点餐识别就能自动带上这些提醒啦。
          </p>
        </div>
      </div>
    </section>
  </section>
</template>
