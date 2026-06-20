<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { LogOut, UserRound } from 'lucide-vue-next'

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
const switchText = computed(() => (mode.value === 'login' ? '还没有账号？去注册' : '已有账号？去登录'))

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
      <p class="text-sm font-semibold text-[#FF7A45]">TaberuMate</p>
      <h1 class="mt-2 text-2xl font-black leading-tight tracking-normal">我的</h1>
    </header>

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
          <p class="mt-2 text-xs font-semibold text-[#667085]">账号已登录，可以开始保存你的旅行点餐偏好。</p>
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
          登录后保存忌口和常用点单备注
        </h2>
        <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
          账号系统使用后端 Access Token、Refresh Token 与 CSRF 双重提交校验。
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
            placeholder="ariakage"
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
  </section>
</template>
