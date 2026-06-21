import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getMenuScanErrorMessage, scanMenuImage } from '@/services/menuScan'
import type { MenuScanResult } from '@/services/menuScan'

const TARGET_LANGUAGE = 'zh-CN'

export const useMenuScanStore = defineStore('menuScan', () => {
  const menuPhotoName = ref('')
  const result = ref<MenuScanResult | null>(null)
  const loading = ref(false)
  const errorMessage = ref('')
  const statusMessage = ref('')

  const hasScannedMenu = computed(() => Boolean(result.value))

  async function scan(file: File) {
    menuPhotoName.value = file.name
    loading.value = true
    errorMessage.value = ''
    statusMessage.value = '正在上传菜单图片...'

    try {
      result.value = await scanMenuImage(
        file,
        TARGET_LANGUAGE,
        (progress) => {
          if (progress === null) {
            statusMessage.value = '正在上传菜单图片...'
            return
          }

          if (progress >= 100) {
            statusMessage.value = '图片已上传，正在识别菜单...'
            return
          }

          statusMessage.value = `正在上传菜单图片... ${progress}%`
        },
        (message) => {
          statusMessage.value = message
        },
      )
      statusMessage.value = '菜单识别完成'
      return true
    } catch (error) {
      errorMessage.value = getMenuScanErrorMessage(error)
      statusMessage.value = ''
      return false
    } finally {
      loading.value = false
    }
  }

  function clearResult() {
    result.value = null
    menuPhotoName.value = ''
    errorMessage.value = ''
    statusMessage.value = ''
  }

  return {
    menuPhotoName,
    result,
    loading,
    errorMessage,
    statusMessage,
    hasScannedMenu,
    scan,
    clearResult,
  }
})
