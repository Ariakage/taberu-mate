<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import {
  ArrowRight,
  Bell,
  Camera,
  X,
  Languages,
  ListChecks,
  ScanText,
  SlidersHorizontal,
} from 'lucide-vue-next'
import { Tag as VanTag } from 'vant'

import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const { appName, japaneseName } = storeToRefs(appStore)

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFileName = ref('')
const recentAvoids = ['花生', '香菜', '生冷海鲜', '太辣']

function openCamera() {
  fileInput.value?.click()
}

function handleMenuPhoto(event: Event) {
  const target = event.target as HTMLInputElement
  selectedFileName.value = target.files?.[0]?.name ?? ''
  appStore.setMenuPhoto(selectedFileName.value)
}
</script>

<template>
  <section class="min-h-dvh bg-transparent px-4 pb-32 text-[#1F2937] pt-[calc(env(safe-area-inset-top)+1rem)]">
    <header class="tm-card relative min-h-[148px] overflow-hidden p-4">
      <div
        class="pointer-events-none absolute bottom-[-36px] right-[-28px] size-36 rounded-full bg-[#FFF1E8]"
        aria-hidden="true"
      ></div>
      <img
        class="pointer-events-none absolute bottom-[-36px] right-[-18px] z-[1] w-[214px] max-w-none select-none drop-shadow-[0_10px_18px_rgba(31,41,55,0.18)]"
        src="/menu-mascot.png"
        alt=""
        aria-hidden="true"
      />
      <div class="flex items-start justify-between gap-4">
        <div class="relative z-10 min-w-0 max-w-[230px] pr-3">
          <p class="text-sm font-semibold tracking-normal text-[#FF7A45]">{{ japaneseName }}</p>
          <h1 class="mt-1 text-[27px] font-black leading-tight tracking-normal text-[#1F2937]">{{ appName }}</h1>
          <p class="mt-2 text-sm font-medium leading-5 text-[#667085]">不怕陌生菜单，陪你旅行吃好饭喵～</p>
        </div>
        <button
          class="relative z-20 grid size-10 shrink-0 place-items-center rounded-lg border border-[#EFDCCC] bg-white/88 text-[#1F2937] backdrop-blur"
          type="button"
          aria-label="通知"
        >
          <Bell :size="20" />
        </button>
      </div>
    </header>

    <main class="mt-4">
      <section class="tm-card overflow-hidden">
        <div class="border-b border-[#F3E3D6] p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <VanTag color="#FFF1E8" text-color="#FF7A45">旅行点餐助手</VanTag>
              <h2 class="mt-3 text-[23px] font-black leading-tight tracking-normal text-[#1F2937]">
                拍下菜单，食べ友帮你看懂喵
              </h2>
              <p class="mt-2 text-sm font-medium leading-5 text-[#667085]">
                选菜、备注忌口，再转成当地语言，给店员看就好。
              </p>
            </div>
            <div class="tm-icon-tile size-11 bg-[#FFF1E8] text-[#FF7A45]">
              <ScanText :size="23" />
            </div>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2 p-4">
          <div class="tm-card-muted p-3">
            <ListChecks class="mb-2 text-[#6BAF92]" :size="18" />
            <p class="text-xs font-black leading-4 text-[#1F2937]">菜单识别</p>
          </div>
          <div class="tm-card-muted p-3">
            <SlidersHorizontal class="mb-2 text-[#8ABFE8]" :size="18" />
            <p class="text-xs font-black leading-4 text-[#1F2937]">忌口筛选</p>
          </div>
          <div class="tm-card-muted p-3">
            <Languages class="mb-2 text-[#FF7A45]" :size="18" />
            <p class="text-xs font-black leading-4 text-[#1F2937]">语言转换</p>
          </div>
        </div>

        <div class="px-4 pb-4">
          <input
            ref="fileInput"
            class="hidden"
            type="file"
            accept="image/*"
            capture="environment"
            @change="handleMenuPhoto"
          />

          <button
            class="flex w-full items-center gap-3 rounded-lg border border-[#FFC8A8] bg-[#FFF1E8] p-3 text-left text-[#1F2937]"
            type="button"
            @click="openCamera"
          >
            <span class="grid size-12 shrink-0 place-items-center rounded-lg bg-[#FF7A45] text-white">
              <Camera :size="24" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block text-base font-black leading-5">拍菜单开始</span>
              <span class="mt-1 block truncate text-xs font-semibold text-[#BA5A32]">
                支持菜单识别、忌口备注和当地语言点单
              </span>
            </span>
            <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-white text-[#FF7A45]">
              <ArrowRight :size="18" />
            </span>
          </button>

          <p
            v-if="selectedFileName"
            class="mt-3 truncate rounded-lg border border-[#CBE5D8] bg-[#F1FAF6] px-3 py-2 text-xs font-semibold text-[#4F8D74]"
          >
            已选择：{{ selectedFileName }}
          </p>

          <div class="mt-3 rounded-lg border border-[#DCECF8] bg-white p-3">
            <p class="text-xs font-black text-[#667085]">给店员看的点菜单</p>
            <p class="mt-1 text-sm font-semibold leading-5 text-[#1F2937]">
              选择想吃的菜，补上忌口和口味备注，一键生成当地语言版本，点菜时直接展示就好。
            </p>
          </div>
        </div>
      </section>

      <section class="tm-card mt-4 p-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-black leading-6 tracking-normal text-[#1F2937]">最近吃过的</h2>
            <p class="mt-1 text-sm font-semibold text-[#667085]">忌口</p>
          </div>
          <div class="rounded-lg border border-[#FFD8D3] bg-[#FFF2F0] px-2.5 py-1 text-xs font-black text-[#D05145]">
            常用备注
          </div>
        </div>

        <div class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="avoid in recentAvoids"
            :key="avoid"
            class="inline-flex items-center gap-1.5 rounded-lg border border-[#FFD8D3] bg-[#FFF2F0] px-3 py-2 text-xs font-black text-[#B95048]"
          >
            <X :size="14" :stroke-width="3" />
            {{ avoid }}
          </span>
        </div>
      </section>
    </main>
  </section>
</template>
