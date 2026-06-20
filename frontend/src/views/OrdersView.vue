<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Camera, ClipboardList, ArrowRight } from 'lucide-vue-next'

import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const { menuPhotoName } = storeToRefs(appStore)
const fileInput = ref<HTMLInputElement | null>(null)

function openCamera() {
  fileInput.value?.click()
}

function handleMenuPhoto(event: Event) {
  const target = event.target as HTMLInputElement
  appStore.setMenuPhoto(target.files?.[0]?.name ?? '')
}
</script>

<template>
  <section class="min-h-dvh bg-transparent px-4 pb-32 text-[#1F2937] pt-[calc(env(safe-area-inset-top)+1rem)]">
    <header class="tm-card mb-4 p-4">
      <p class="text-sm font-semibold text-[#FF7A45]">TaberuMate</p>
      <h1 class="mt-2 text-2xl font-black leading-tight tracking-normal">点单</h1>
    </header>

    <section v-if="!menuPhotoName" class="tm-card p-4">
      <input
        ref="fileInput"
        class="hidden"
        type="file"
        accept="image/*"
        capture="environment"
        @change="handleMenuPhoto"
      />

      <div class="grid min-h-[280px] place-items-center text-center">
        <div class="max-w-[280px]">
          <div class="mx-auto grid size-16 place-items-center rounded-lg bg-[#FFF1E8] text-[#FF7A45]">
            <Camera :size="30" />
          </div>
          <h2 class="mt-5 text-2xl font-black leading-tight tracking-normal">还没有拍摄菜单</h2>
          <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
            拍下当地菜单后，食べ友才能帮你识别菜品、筛选忌口并生成点菜单。
          </p>

          <button
            class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-[#FFC8A8] bg-[#FFF1E8] px-4 py-3 text-sm font-black text-[#1F2937]"
            type="button"
            @click="openCamera"
          >
            现在去拍摄吧！
            <ArrowRight :size="17" />
          </button>
        </div>
      </div>
    </section>

    <section v-else class="tm-card p-4">
      <div class="flex items-start gap-3">
        <div class="tm-icon-tile bg-[#FFF1E8] text-[#FF7A45]">
          <ClipboardList :size="21" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-xs font-black text-[#667085]">已拍摄菜单</p>
          <h2 class="mt-1 truncate text-lg font-black text-[#1F2937]">{{ menuPhotoName }}</h2>
          <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
            菜单已准备好，下一步可以进入识别、选菜和备注忌口流程。
          </p>
        </div>
      </div>
    </section>
  </section>
</template>
