<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Empty as VanEmpty } from 'vant'

const route = useRoute()
const title = computed(() => String(route.meta.title ?? '页面'))
</script>

<template>
  <section
    class="flex min-h-dvh flex-col bg-transparent px-4 pb-28 pt-[calc(env(safe-area-inset-top)+1rem)]"
  >
    <header class="tm-card mb-4 p-4">
      <p class="text-sm font-semibold text-[#FF7A45]">TaberuMate</p>
      <h1 class="mt-2 text-2xl font-bold text-[#1F2937]">{{ title }}</h1>
    </header>

    <div class="tm-card flex flex-1 items-center justify-center px-4">
      <VanEmpty image="search" :description="`${title}功能正在准备中`" />
    </div>
  </section>
</template>
