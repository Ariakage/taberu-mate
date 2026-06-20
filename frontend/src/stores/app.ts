import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export interface MealPlanItem {
  id: string
  time: string
  title: string
  note: string
  kcal: number
  accent: 'orange' | 'green' | 'blue'
}

export interface CompanionPick {
  id: string
  title: string
  place: string
  match: number
}

export const useAppStore = defineStore('app', () => {
  const appName = ref('TaberuMate')
  const japaneseName = ref('食べ友')
  const checkedIn = ref(false)
  const menuPhotoName = ref('')

  const todayTargetKcal = ref(1800)
  const consumedKcal = ref(860)
  const matesOnline = ref(6)

  const mealPlan = ref<MealPlanItem[]>([
    {
      id: 'breakfast',
      time: '08:20',
      title: '燕麦酸奶杯',
      note: '坚果、蓝莓、无糖酸奶',
      kcal: 360,
      accent: 'orange',
    },
    {
      id: 'lunch',
      time: '12:30',
      title: '鸡肉蔬菜便当',
      note: '糙米、烤南瓜、青豆',
      kcal: 620,
      accent: 'green',
    },
    {
      id: 'dinner',
      time: '19:00',
      title: '豆腐海苔汤',
      note: '配小份荞麦面',
      kcal: 520,
      accent: 'blue',
    },
  ])

  const companionPicks = ref<CompanionPick[]>([
    {
      id: 'udon',
      title: '番茄牛肉乌冬',
      place: '适合两人晚餐',
      match: 92,
    },
    {
      id: 'bento',
      title: '照烧鸡腿饭',
      place: '午休便当优先',
      match: 88,
    },
    {
      id: 'salad',
      title: '鲜虾藜麦沙拉',
      place: '轻食日推荐',
      match: 84,
    },
  ])

  const progressPercent = computed(() =>
    Math.min(100, Math.round((consumedKcal.value / todayTargetKcal.value) * 100)),
  )

  function toggleCheckIn() {
    checkedIn.value = !checkedIn.value
  }

  function setMenuPhoto(name: string) {
    menuPhotoName.value = name
  }

  return {
    appName,
    japaneseName,
    checkedIn,
    menuPhotoName,
    todayTargetKcal,
    consumedKcal,
    matesOnline,
    mealPlan,
    companionPicks,
    progressPercent,
    toggleCheckIn,
    setMenuPhoto,
  }
})
