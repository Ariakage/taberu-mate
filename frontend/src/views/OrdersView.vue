<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  ArrowRight,
  Camera,
  ChefHat,
  Check,
  ClipboardList,
  MessageSquareText,
  Minus,
  Plus,
  RotateCcw,
  ShoppingBag,
  Sparkles,
  X,
} from 'lucide-vue-next'
import { showToast } from 'vant'

import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useMenuScanStore } from '@/stores/menuScan'
import { useUserProfileStore } from '@/stores/userProfile'
import {
  generateOrderMenu,
  getOrderAssistantErrorMessage,
  type GenerateOrderMenuInput,
  type GeneratedOrderMenu,
} from '@/services/orderAssistant'
import type {
  MenuScanCategory,
  MenuScanConfidence,
  MenuScanItem,
  MenuScanPrice,
  MenuScanTasteProfile,
} from '@/services/menuScan'

const appStore = useAppStore()
const authStore = useAuthStore()
const menuScanStore = useMenuScanStore()
const userProfileStore = useUserProfileStore()
const { errorMessage, hasScannedMenu, loading, menuPhotoName, result, statusMessage } =
  storeToRefs(menuScanStore)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedCategoryId = ref('all')
const itemQuantities = ref<Record<string, number>>({})
const selectedTasteFilters = ref<string[]>([])
const selectedAvoidanceFilters = ref<string[]>([])
const isOrderNoteOpen = ref(false)
const orderRemark = ref('')
const selectedOrderLanguage = ref('')
const generatedOrderMenu = ref<GeneratedOrderMenu | null>(null)
const orderGenerationError = ref('')
const isGeneratingOrder = ref(false)

type AllergenLanguageKey = 'zh' | 'ja' | 'ko' | 'en'
type OrderLanguageOption = {
  code: string
  label: string
  instruction: string
}
type TasteLevelKey = keyof MenuScanTasteProfile
type TasteFilterOption = {
  id: string
  label: string
  keys?: TasteLevelKey[]
  min?: number
  tokens?: string[]
}
type AvoidanceFilterOption = {
  id: string
  label: string
  allergenIds?: string[]
  dietaryKeys?: Array<keyof NonNullable<MenuScanItem['dietary']>>
  tokens?: string[]
}

const WEEKDAY_LABELS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const ORDER_NOTE_PRESETS = ['不要香菜', '少辣', '不要葱蒜', '酱料分开', '少油少盐', '有过敏请确认']
const ORDER_LANGUAGE_OPTIONS: OrderLanguageOption[] = [
  { code: 'zh-CN', label: '中文简体', instruction: 'Simplified Chinese (zh-CN)' },
  { code: 'yue-HK', label: '香港粤语', instruction: 'Hong Kong Cantonese (yue-HK)' },
  { code: 'hak-TW', label: '台湾客家话', instruction: 'Taiwanese Hakka (hak-TW)' },
  { code: 'en-GB', label: '英文 UK', instruction: 'English UK (en-GB)' },
  { code: 'en-US', label: '英文 US', instruction: 'English US (en-US)' },
  { code: 'ja', label: '日语', instruction: 'Japanese (ja)' },
  { code: 'ko', label: '韩语', instruction: 'Korean (ko)' },
  { code: 'th-TH', label: '泰国语言', instruction: 'Thai (th-TH)' },
]
const TASTE_FILTER_OPTIONS: TasteFilterOption[] = [
  {
    id: 'spicy',
    label: '辣味',
    keys: ['spicy_level'],
    min: 2,
    tokens: ['spicy', 'hot', '辣', '辛', '麻婆'],
  },
  { id: 'sweet', label: '甜口', keys: ['sweet_level'], min: 2, tokens: ['sweet', '甜', '甘'] },
  { id: 'sour', label: '酸味', keys: ['sour_level'], min: 2, tokens: ['sour', '酸'] },
  {
    id: 'rich',
    label: '浓郁',
    keys: ['richness_level'],
    min: 3,
    tokens: ['rich', '浓', '濃', 'こってり'],
  },
  {
    id: 'salty',
    label: '咸鲜',
    keys: ['salty_level'],
    min: 3,
    tokens: ['salty', '咸', '盐', '塩'],
  },
  { id: 'mild', label: '清淡', tokens: ['mild', 'light', '清淡', 'さっぱり'] },
]
const AVOIDANCE_FILTER_OPTIONS: AvoidanceFilterOption[] = [
  { id: 'gluten', label: '麸质', allergenIds: ['gluten'], tokens: ['gluten', '麸质', '小麦'] },
  { id: 'peanuts', label: '花生', allergenIds: ['peanuts'], tokens: ['peanut', '花生'] },
  { id: 'tree_nuts', label: '坚果', allergenIds: ['tree_nuts'], tokens: ['nut', 'nuts', '坚果'] },
  { id: 'eggs', label: '鸡蛋', allergenIds: ['eggs'], tokens: ['egg', '鸡蛋', '玉子', '卵'] },
  { id: 'milk', label: '牛奶', allergenIds: ['milk'], tokens: ['milk', '奶', '乳'] },
  { id: 'soybeans', label: '大豆', allergenIds: ['soybeans'], tokens: ['soy', '大豆'] },
  {
    id: 'seafood',
    label: '海鲜',
    allergenIds: ['crustaceans', 'fish', 'molluscs'],
    dietaryKeys: ['contains_seafood'],
    tokens: ['seafood', 'shrimp', 'fish', '海鲜', '海鮮', '虾', '魚', '鱼', 'エビ'],
  },
  { id: 'pork', label: '猪肉', dietaryKeys: ['contains_pork'], tokens: ['pork', '猪', '豚'] },
  { id: 'beef', label: '牛肉', dietaryKeys: ['contains_beef'], tokens: ['beef', '牛'] },
  {
    id: 'chicken',
    label: '鸡肉',
    dietaryKeys: ['contains_chicken'],
    tokens: ['chicken', '鸡', '鶏'],
  },
  { id: 'alcohol', label: '酒精', dietaryKeys: ['contains_alcohol'], tokens: ['alcohol', '酒'] },
]
const WEEKDAY_MATCHERS = [
  {
    day: 0,
    tokens: ['sunday', 'sun', '日曜日', '星期日', '星期天', '周日', '週日', '周天', '週天'],
  },
  { day: 1, tokens: ['monday', 'mon', '月曜日', '星期一', '周一', '週一', '礼拜一'] },
  { day: 2, tokens: ['tuesday', 'tue', '火曜日', '星期二', '周二', '週二', '礼拜二'] },
  { day: 3, tokens: ['wednesday', 'wed', '水曜日', '星期三', '周三', '週三', '礼拜三'] },
  { day: 4, tokens: ['thursday', 'thu', '木曜日', '星期四', '周四', '週四', '礼拜四'] },
  { day: 5, tokens: ['friday', 'fri', '金曜日', '星期五', '周五', '週五', '礼拜五'] },
  { day: 6, tokens: ['saturday', 'sat', '土曜日', '星期六', '周六', '週六', '礼拜六'] },
]

const ALLERGEN_TRANSLATIONS: Record<string, Record<AllergenLanguageKey, string>> = {
  gluten: { zh: '麸质', ja: 'グルテン', ko: '글루텐', en: 'gluten' },
  crustaceans: { zh: '甲壳类', ja: '甲殻類', ko: '갑각류', en: 'crustaceans' },
  eggs: { zh: '鸡蛋', ja: '卵', ko: '달걀', en: 'eggs' },
  fish: { zh: '鱼类', ja: '魚', ko: '생선', en: 'fish' },
  peanuts: { zh: '花生', ja: 'ピーナッツ', ko: '땅콩', en: 'peanuts' },
  soybeans: { zh: '大豆', ja: '大豆', ko: '대두', en: 'soybeans' },
  milk: { zh: '牛奶', ja: '乳', ko: '우유', en: 'milk' },
  tree_nuts: { zh: '坚果', ja: '木の実', ko: '견과류', en: 'tree nuts' },
  celery: { zh: '芹菜', ja: 'セロリ', ko: '셀러리', en: 'celery' },
  mustard: { zh: '芥末', ja: 'マスタード', ko: '겨자', en: 'mustard' },
  sesame: { zh: '芝麻', ja: 'ごま', ko: '참깨', en: 'sesame' },
  sulfites: { zh: '亚硫酸盐', ja: '亜硫酸塩', ko: '아황산염', en: 'sulfites' },
  lupin: { zh: '羽扇豆', ja: 'ルピナス', ko: '루핀', en: 'lupin' },
  molluscs: { zh: '软体贝类', ja: '軟体動物', ko: '연체동물', en: 'molluscs' },
  alcohol: { zh: '酒精', ja: 'アルコール', ko: '알코올', en: 'alcohol' },
  unknown: { zh: '未知', ja: '不明', ko: '알 수 없음', en: 'unknown' },
}

const sortedCategories = computed(() =>
  [...(result.value?.categories ?? [])].sort(
    (left, right) => (left.sort_order ?? 999) - (right.sort_order ?? 999),
  ),
)

const categoryTabs = computed(() => {
  const items = result.value?.items ?? []

  return [
    {
      id: 'all',
      label: '全部',
      count: items.length,
    },
    ...sortedCategories.value.map((category) => ({
      id: category.id,
      label: getCategoryName(category),
      count: items.filter((item) => isItemInCategory(item, category.id)).length,
    })),
  ].filter((category) => category.id === 'all' || category.count > 0)
})

const categoryFilteredItems = computed(() => {
  const items = result.value?.items ?? []

  if (selectedCategoryId.value === 'all') {
    return items
  }

  return items.filter((item) => isItemInCategory(item, selectedCategoryId.value))
})

const filteredItems = computed(() =>
  categoryFilteredItems.value.filter(
    (item) => matchesTasteFilters(item) && matchesAvoidanceFilters(item),
  ),
)

const menuTitle = computed(
  () =>
    result.value?.menu.restaurant_name_translated ||
    result.value?.menu.restaurant_name_original ||
    menuPhotoName.value ||
    '识别菜单',
)
const targetLanguage = computed(() => result.value?.menu.target_language || 'zh-CN')
const targetLanguageLabel = computed(() => formatTargetLanguage(targetLanguage.value))
const todayWeekday = computed(() => new Date().getDay())
const todayWeekdayLabel = computed(() => formatWeekdayName(todayWeekday.value))
const categoryById = computed(
  () => new Map((result.value?.categories ?? []).map((category) => [category.id, category])),
)

const selectedOrderLines = computed(() =>
  (result.value?.items ?? [])
    .map((item) => ({
      item,
      quantity: getItemQuantity(item),
    }))
    .filter((line) => line.quantity > 0),
)

const orderItemCount = computed(() =>
  selectedOrderLines.value.reduce((count, line) => count + line.quantity, 0),
)

const orderCurrency = computed(
  () =>
    selectedOrderLines.value.find((line) => line.item.price?.currency)?.item.price?.currency ||
    result.value?.menu.currency ||
    '',
)

const orderTotalAmount = computed(() =>
  selectedOrderLines.value.reduce(
    (total, line) => total + getItemPriceAmount(line.item) * line.quantity,
    0,
  ),
)

const orderTotalLabel = computed(() => formatMoney(orderTotalAmount.value, orderCurrency.value))
const hasOrderItems = computed(() => orderItemCount.value > 0)
const activeFilterCount = computed(
  () => selectedTasteFilters.value.length + selectedAvoidanceFilters.value.length,
)
const hasActiveMenuFilters = computed(() => activeFilterCount.value > 0)
const selectedOrderLanguageOption = computed(
  () =>
    ORDER_LANGUAGE_OPTIONS.find((language) => language.code === selectedOrderLanguage.value) ??
    null,
)

watch(result, () => {
  selectedCategoryId.value = 'all'
  itemQuantities.value = {}
  selectedTasteFilters.value = []
  selectedAvoidanceFilters.value = []
  isOrderNoteOpen.value = false
  orderRemark.value = ''
  selectedOrderLanguage.value = ''
  generatedOrderMenu.value = null
  orderGenerationError.value = ''
})

watch([itemQuantities, orderRemark, selectedOrderLanguage], () => {
  generatedOrderMenu.value = null
  orderGenerationError.value = ''
})

function openCamera() {
  if (!loading.value) {
    fileInput.value?.click()
  }
}

async function handleMenuPhoto(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) {
    return
  }

  target.value = ''
  await authStore.initialize()

  if (!authStore.isAuthenticated) {
    showToast('需要登录才能使用菜单识别')
    return
  }

  appStore.setMenuPhoto(file.name)

  const scanned = await menuScanStore.scan(file)

  if (!scanned) {
    showToast(errorMessage.value || '菜单识别失败，请稍后再试')
    return
  }

  showToast('菜单识别完成')
}

function getCategoryName(category: MenuScanCategory) {
  return category.name_translated || category.name_original || '未分类'
}

function isItemInCategory(item: MenuScanItem, categoryId: string) {
  return item.primary_category_id === categoryId || item.category_ids?.includes(categoryId)
}

function formatPrice(price?: MenuScanPrice | null) {
  if (!price) {
    return '价格待确认'
  }

  if (price.raw_text) {
    return price.raw_text
  }

  if (typeof price.amount === 'number') {
    return `${price.currency ?? ''} ${price.amount}`.trim()
  }

  return '价格待确认'
}

function getItemPriceAmount(item: MenuScanItem) {
  return typeof item.price?.amount === 'number' ? item.price.amount : 0
}

function formatMoney(amount: number, currency?: string | null) {
  const normalizedCurrency = currency?.toUpperCase()
  const roundedAmount = Number.isInteger(amount) ? `${amount}` : amount.toFixed(2)

  if (
    normalizedCurrency === 'JPY' ||
    normalizedCurrency === 'CNY' ||
    normalizedCurrency === 'RMB'
  ) {
    return `¥${roundedAmount}`
  }

  if (normalizedCurrency === 'USD') {
    return `$${roundedAmount}`
  }

  if (normalizedCurrency === 'EUR') {
    return `€${roundedAmount}`
  }

  if (normalizedCurrency === 'GBP') {
    return `£${roundedAmount}`
  }

  if (normalizedCurrency === 'KRW') {
    return `₩${roundedAmount}`
  }

  return normalizedCurrency ? `${normalizedCurrency} ${roundedAmount}` : roundedAmount
}

function canOrderItem(item: MenuScanItem) {
  return resolveItemAvailability(item).orderable
}

function getItemQuantity(item: MenuScanItem) {
  return itemQuantities.value[item.id] ?? 0
}

function setItemQuantity(item: MenuScanItem, quantity: number) {
  const safeQuantity = Math.max(0, Math.min(99, quantity))
  const nextQuantities = { ...itemQuantities.value }

  if (safeQuantity > 0) {
    nextQuantities[item.id] = safeQuantity
  } else {
    delete nextQuantities[item.id]
  }

  itemQuantities.value = nextQuantities
}

function addItem(item: MenuScanItem) {
  if (!canOrderItem(item)) {
    showToast('这道菜当前不可点')
    return
  }

  setItemQuantity(item, getItemQuantity(item) + 1)
}

function removeItem(item: MenuScanItem) {
  setItemQuantity(item, getItemQuantity(item) - 1)
}

function toggleTasteFilter(filterId: string) {
  selectedTasteFilters.value = toggleArrayValue(selectedTasteFilters.value, filterId)
}

function toggleAvoidanceFilter(filterId: string) {
  selectedAvoidanceFilters.value = toggleArrayValue(selectedAvoidanceFilters.value, filterId)
}

function clearMenuFilters() {
  selectedTasteFilters.value = []
  selectedAvoidanceFilters.value = []
}

function toggleArrayValue(values: string[], value: string) {
  if (values.includes(value)) {
    return values.filter((item) => item !== value)
  }

  return [...values, value]
}

function openOrderNote() {
  if (!hasOrderItems.value) {
    showToast('请先选择菜品')
    return
  }

  orderGenerationError.value = ''
  isOrderNoteOpen.value = true
}

function closeOrderNote() {
  isOrderNoteOpen.value = false
}

function appendOrderNotePreset(note: string) {
  const currentNotes = orderRemark.value
    .split(/[，,\n]/)
    .map((item) => item.trim())
    .filter(Boolean)

  if (currentNotes.includes(note)) {
    return
  }

  orderRemark.value = [...currentNotes, note].join('，')
}

function clearOrderRemark() {
  orderRemark.value = ''
}

function selectOrderLanguage(languageCode: string) {
  selectedOrderLanguage.value = languageCode
}

function buildOrderMenuInput(): GenerateOrderMenuInput {
  const languageOption = selectedOrderLanguageOption.value

  return {
    restaurant_name_original: result.value?.menu.restaurant_name_original ?? null,
    restaurant_name_translated: result.value?.menu.restaurant_name_translated ?? null,
    source_language: result.value?.menu.source_language,
    target_language: languageOption?.instruction ?? '',
    target_language_code: languageOption?.code,
    currency: orderCurrency.value || result.value?.menu.currency || undefined,
    customer_remark: orderRemark.value.trim(),
    total_amount: orderTotalAmount.value,
    total_label: orderTotalLabel.value,
    items: selectedOrderLines.value.map(({ item, quantity }) => ({
      id: item.id,
      name_original: item.name_original ?? null,
      name_translated: item.name_translated ?? null,
      quantity,
      price: item.price ?? null,
      tags: item.tags ?? [],
    })),
  }
}

function buildOrderHistoryPayload(
  input: GenerateOrderMenuInput,
  generatedOrder: GeneratedOrderMenu,
) {
  return {
    restaurant_name:
      input.restaurant_name_translated ||
      input.restaurant_name_original ||
      menuPhotoName.value ||
      null,
    target_language: input.target_language_code || input.target_language || null,
    customer_remark: input.customer_remark,
    total_amount: input.total_amount,
    total_label: input.total_label,
    items: input.items.map((item) => ({ ...item })) as Array<Record<string, unknown>>,
    generated_order: generatedOrder as unknown as Record<string, unknown>,
  }
}

function formatAvailability(item: MenuScanItem) {
  return resolveItemAvailability(item).label
}

function matchesTasteFilters(item: MenuScanItem) {
  if (!selectedTasteFilters.value.length) {
    return true
  }

  return selectedTasteFilters.value.some((filterId) => matchesTasteFilter(item, filterId))
}

function matchesTasteFilter(item: MenuScanItem, filterId: string) {
  const option = TASTE_FILTER_OPTIONS.find((filterOption) => filterOption.id === filterId)
  if (!option) {
    return true
  }

  const searchText = getItemSearchText(item)
  const tokenMatched =
    option.tokens?.some((token) => searchText.includes(token.toLowerCase())) ?? false

  if (filterId === 'mild') {
    if (tokenMatched) {
      return true
    }

    if (!hasTasteProfile(item)) {
      return false
    }

    return (
      getTasteLevel(item, 'spicy_level') <= 1 &&
      getTasteLevel(item, 'salty_level') <= 2 &&
      getTasteLevel(item, 'richness_level') <= 2
    )
  }

  const levelMatched =
    option.keys?.some((key) => getTasteLevel(item, key) >= (option.min ?? 1)) ?? false

  return levelMatched || tokenMatched
}

function matchesAvoidanceFilters(item: MenuScanItem) {
  return selectedAvoidanceFilters.value.every((filterId) => !matchesAvoidanceFilter(item, filterId))
}

function matchesAvoidanceFilter(item: MenuScanItem, filterId: string) {
  const option = AVOIDANCE_FILTER_OPTIONS.find((filterOption) => filterOption.id === filterId)
  if (!option) {
    return false
  }

  const itemAllergens = new Set((item.allergens ?? []).map((allergen) => allergen.toLowerCase()))
  const allergenMatched =
    option.allergenIds?.some((allergen) => itemAllergens.has(allergen.toLowerCase())) ?? false
  const dietaryMatched = option.dietaryKeys?.some((key) => item.dietary?.[key] === true) ?? false
  const searchText = getItemSearchText(item)
  const tokenMatched =
    option.tokens?.some((token) => searchText.includes(token.toLowerCase())) ?? false

  return allergenMatched || dietaryMatched || tokenMatched
}

function getTasteLevel(item: MenuScanItem, key: TasteLevelKey) {
  const value = item.taste_profile?.[key]
  return typeof value === 'number' ? value : 0
}

function hasTasteProfile(item: MenuScanItem) {
  return Object.values(item.taste_profile ?? {}).some((value) => typeof value === 'number')
}

function getItemSearchText(item: MenuScanItem) {
  return [
    item.name_original,
    item.name_translated,
    item.description_original,
    item.description_translated,
    ...(item.tags ?? []),
    ...(item.allergens ?? []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function resolveItemAvailability(item: MenuScanItem) {
  const status = item.availability?.status

  if (status === 'sold_out') {
    return {
      label: '售罄',
      orderable: false,
      tone: 'unavailable',
    }
  }

  const weekdays = getItemWeekdayRestrictions(item)
  if (weekdays.length && !weekdays.includes(todayWeekday.value)) {
    return {
      label: `今日不可点 · ${formatWeekdayList(weekdays)}限定`,
      orderable: false,
      tone: 'unavailable',
    }
  }

  if (weekdays.length) {
    return {
      label: '今日可点',
      orderable: true,
      tone: 'available',
    }
  }

  if (status === 'limited') {
    return {
      label: item.availability?.note || '限量',
      orderable: true,
      tone: 'limited',
    }
  }

  return {
    label: item.availability?.note || '可点',
    orderable: true,
    tone: 'available',
  }
}

function availabilityClass(item: MenuScanItem) {
  const availability = resolveItemAvailability(item)

  if (availability.tone === 'unavailable') {
    return 'border-[#FFD8D3] bg-[#FFF2F0] text-[#B95048]'
  }

  if (availability.tone === 'limited') {
    return 'border-[#FFE2A8] bg-[#FFF8E8] text-[#A66B00]'
  }

  return 'border-[#CBE5D8] bg-[#F1FAF6] text-[#4F8D74]'
}

function getItemWeekdayRestrictions(item: MenuScanItem) {
  const weekdays = new Set<number>()
  const categoryIds = new Set(
    [item.primary_category_id, ...(item.category_ids ?? [])].filter(
      (categoryId): categoryId is string => typeof categoryId === 'string' && categoryId.length > 0,
    ),
  )

  for (const categoryId of categoryIds) {
    const category = categoryById.value.get(categoryId)
    if (!category) {
      continue
    }

    for (const weekday of getWeekdaysFromText(
      [category.id, category.name_original, category.name_translated].filter(Boolean).join(' '),
    )) {
      weekdays.add(weekday)
    }
  }

  for (const weekday of getWeekdaysFromText(item.availability?.note ?? '')) {
    weekdays.add(weekday)
  }

  return [...weekdays].sort((left, right) => left - right)
}

function getWeekdaysFromText(text: string) {
  const normalized = text.toLowerCase().replace(/\s+/g, '')
  return WEEKDAY_MATCHERS.filter(({ tokens }) =>
    tokens.some((token) => normalized.includes(token.toLowerCase())),
  ).map(({ day }) => day)
}

function formatWeekdayList(weekdays: number[]) {
  return weekdays.map((weekday) => formatWeekdayName(weekday)).join('、')
}

function formatWeekdayName(weekday: number) {
  return WEEKDAY_LABELS[weekday] ?? '未知日期'
}

function formatTargetLanguage(language: string) {
  const normalized = language.toLowerCase()

  if (normalized === 'zh-cn' || normalized.includes('简体')) {
    return '简体中文'
  }

  if (normalized === 'zh-tw' || normalized === 'zh-hk' || normalized.includes('繁体')) {
    return '繁体中文'
  }

  if (normalized.startsWith('ja')) {
    return '日语'
  }

  if (normalized.startsWith('ko')) {
    return '韩语'
  }

  if (normalized.startsWith('en')) {
    return '英语'
  }

  return language
}

function translatedAllergens(item: MenuScanItem) {
  return (item.allergens ?? []).map((allergen) => translateAllergen(allergen, targetLanguage.value))
}

function translateAllergen(allergen: string, language: string) {
  const languageKey = getAllergenLanguageKey(language)
  const translations = ALLERGEN_TRANSLATIONS[allergen]

  if (translations?.[languageKey]) {
    return translations[languageKey]
  }

  return allergen.replace(/_/g, ' ')
}

function getAllergenLanguageKey(language: string) {
  const normalized = language.toLowerCase()

  if (normalized.startsWith('ja')) {
    return 'ja'
  }

  if (normalized.startsWith('ko')) {
    return 'ko'
  }

  if (normalized.startsWith('en')) {
    return 'en'
  }

  return 'zh'
}

function confidencePercent(confidence?: MenuScanConfidence | null) {
  const values = Object.values(confidence ?? {}).filter(
    (value): value is number => typeof value === 'number',
  )

  if (!values.length) {
    return '--'
  }

  const average = values.reduce((sum, value) => sum + value, 0) / values.length
  return `${Math.round(average * 100)}%`
}

function confidenceEntries(confidence?: MenuScanConfidence | null) {
  const labels: Array<[keyof MenuScanConfidence, string]> = [
    ['ocr', 'OCR'],
    ['translation', '翻译'],
    ['classification', '分类'],
    ['price_detection', '价格'],
    ['allergen_detection', '过敏'],
  ]

  return labels
    .map(([key, label]) => {
      const value = confidence?.[key]

      if (typeof value !== 'number') {
        return null
      }

      return {
        key,
        label,
        value: `${Math.round(value * 100)}%`,
      }
    })
    .filter((entry): entry is { key: keyof MenuScanConfidence; label: string; value: string } =>
      Boolean(entry),
    )
}

async function submitOrder() {
  if (!hasOrderItems.value) {
    showToast('请先选择菜品')
    return
  }

  if (!selectedOrderLanguageOption.value) {
    orderGenerationError.value = '请选择点菜单语言'
    showToast(orderGenerationError.value)
    return
  }

  isGeneratingOrder.value = true
  orderGenerationError.value = ''

  try {
    const orderInput = buildOrderMenuInput()
    generatedOrderMenu.value = await generateOrderMenu(orderInput)

    if (authStore.isAuthenticated) {
      try {
        await userProfileStore.saveOrderHistory(
          buildOrderHistoryPayload(orderInput, generatedOrderMenu.value),
        )
        showToast('AI 点菜单已生成，已保存历史')
      } catch {
        showToast('AI 点菜单已生成，历史保存失败')
      }
      return
    }

    showToast('AI 点菜单已生成')
  } catch (error) {
    orderGenerationError.value = getOrderAssistantErrorMessage(error)
    showToast(orderGenerationError.value)
  } finally {
    isGeneratingOrder.value = false
  }
}
</script>

<template>
  <section
    class="min-h-dvh bg-transparent px-4 pb-40 text-[#1F2937] pt-[calc(env(safe-area-inset-top)+1rem)]"
  >
    <input
      ref="fileInput"
      class="hidden"
      type="file"
      accept="image/*"
      capture="environment"
      @change="handleMenuPhoto"
    />

    <header class="tm-card mb-4 p-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="text-sm font-semibold text-[#FF7A45]">食べ友</p>
          <h1 class="mt-2 text-2xl font-black leading-tight tracking-normal">
            {{ hasScannedMenu ? '菜单' : '点单' }}
          </h1>
        </div>

        <button
          v-if="hasScannedMenu"
          class="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-[#FFC8A8] bg-[#FFF1E8] px-3 py-2 text-xs font-black text-[#BA5A32] disabled:opacity-60"
          type="button"
          :disabled="loading"
          @click="openCamera"
        >
          <RotateCcw :size="15" />
          拍新的菜单
        </button>
      </div>
    </header>

    <section v-if="!hasScannedMenu" class="tm-card p-4">
      <div class="grid min-h-[280px] place-items-center text-center">
        <div class="max-w-[280px]">
          <div
            class="mx-auto grid size-16 place-items-center rounded-lg bg-[#FFF1E8] text-[#FF7A45]"
          >
            <Camera :size="30" />
          </div>
          <h2 class="mt-5 text-2xl font-black leading-tight tracking-normal">还没有拍摄菜单</h2>
          <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
            拍下当地菜单后，食べ友会先确认登录，再识别菜品、分类和置信度。
          </p>

          <button
            class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-[#FFC8A8] bg-[#FFF1E8] px-4 py-3 text-sm font-black text-[#1F2937] disabled:opacity-60"
            type="button"
            :disabled="loading"
            @click="openCamera"
          >
            {{ loading ? '正在识别菜单...' : '现在去拍摄吧！' }}
            <ArrowRight :size="17" />
          </button>

          <p
            v-if="errorMessage || statusMessage"
            class="mt-3 rounded-lg border px-3 py-2 text-xs font-black"
            :class="
              errorMessage
                ? 'border-[#FFD8D3] bg-[#FFF2F0] text-[#B95048]'
                : 'border-[#DCECF8] bg-white text-[#4C7CA3]'
            "
          >
            {{ errorMessage || statusMessage }}
          </p>
        </div>
      </div>
    </section>

    <template v-else>
      <section class="tm-card mb-4 overflow-hidden">
        <div class="border-b border-[#F3E3D6] p-4">
          <div class="flex items-start gap-3">
            <div class="tm-icon-tile bg-[#FFF1E8] text-[#FF7A45]">
              <ChefHat :size="22" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-xs font-black text-[#667085]">识别完成</p>
              <h2 class="mt-1 truncate text-xl font-black leading-6 text-[#1F2937]">
                {{ menuTitle }}
              </h2>
              <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
                目标语言：{{ targetLanguageLabel }} · 今天{{ todayWeekdayLabel }} · 共识别
                {{ result?.items.length ?? 0 }} 道菜
              </p>
            </div>
          </div>

          <p
            v-if="loading"
            class="mt-3 rounded-lg border border-[#DCECF8] bg-white px-3 py-2 text-xs font-black text-[#4C7CA3]"
          >
            {{ statusMessage || '正在识别新的菜单，请稍等...' }}
          </p>

          <div class="mt-4 rounded-lg border border-[#F3E3D6] bg-[#FFFAF4] p-3">
            <div class="flex items-center justify-between gap-3">
              <div class="min-w-0">
                <p class="text-sm font-black leading-5 text-[#1F2937]">筛选</p>
                <p class="mt-0.5 text-[11px] font-semibold text-[#667085]">
                  {{ filteredItems.length }} / {{ categoryFilteredItems.length }} 道
                </p>
              </div>
              <button
                v-if="hasActiveMenuFilters"
                class="shrink-0 rounded-lg border border-[#EFDCCC] bg-white px-2.5 py-1.5 text-xs font-black text-[#667085]"
                type="button"
                @click="clearMenuFilters"
              >
                清空
              </button>
            </div>

            <div class="mt-3">
              <p class="mb-2 text-xs font-black text-[#667085]">口味</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="filter in TASTE_FILTER_OPTIONS"
                  :key="filter.id"
                  class="rounded-lg border px-3 py-2 text-xs font-black transition"
                  :class="
                    selectedTasteFilters.includes(filter.id)
                      ? 'border-[#FF7A45] bg-[#FFF1E8] text-[#BA5A32]'
                      : 'border-[#EFDCCC] bg-white text-[#667085]'
                  "
                  type="button"
                  :aria-pressed="selectedTasteFilters.includes(filter.id)"
                  @click="toggleTasteFilter(filter.id)"
                >
                  {{ filter.label }}
                </button>
              </div>
            </div>

            <div class="mt-3">
              <p class="mb-2 text-xs font-black text-[#667085]">过敏忌口</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="filter in AVOIDANCE_FILTER_OPTIONS"
                  :key="filter.id"
                  class="rounded-lg border px-3 py-2 text-xs font-black transition"
                  :class="
                    selectedAvoidanceFilters.includes(filter.id)
                      ? 'border-[#FFD8D3] bg-[#FFF2F0] text-[#B95048]'
                      : 'border-[#EFDCCC] bg-white text-[#667085]'
                  "
                  type="button"
                  :aria-pressed="selectedAvoidanceFilters.includes(filter.id)"
                  @click="toggleAvoidanceFilter(filter.id)"
                >
                  {{ filter.label }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="flex min-h-[420px]">
          <aside class="w-[92px] shrink-0 border-r border-[#F3E3D6] bg-[#FFFAF4] p-2">
            <button
              v-for="category in categoryTabs"
              :key="category.id"
              class="mb-2 flex w-full flex-col items-start rounded-lg px-2 py-2 text-left text-xs font-black leading-4 transition"
              :class="
                selectedCategoryId === category.id
                  ? 'bg-[#FF7A45] text-white'
                  : 'border border-[#F3E3D6] bg-white text-[#667085]'
              "
              type="button"
              @click="selectedCategoryId = category.id"
            >
              <span class="line-clamp-2">{{ category.label }}</span>
              <span class="mt-1 text-[10px] opacity-80">{{ category.count }} 道</span>
            </button>
          </aside>

          <div class="min-w-0 flex-1 space-y-3 p-3">
            <article v-for="item in filteredItems" :key="item.id" class="tm-card-muted p-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                  <h3 class="text-base font-black leading-5 text-[#1F2937]">
                    {{ item.name_translated || item.name_original || '未命名菜品' }}
                  </h3>
                  <p
                    v-if="item.name_original"
                    class="mt-1 truncate text-xs font-semibold text-[#667085]"
                  >
                    {{ item.name_original }}
                  </p>
                </div>
                <div class="flex w-[92px] shrink-0 flex-col items-end gap-2">
                  <p
                    class="max-w-full break-words text-right text-sm font-black leading-4 text-[#FF7A45]"
                  >
                    {{ formatPrice(item.price) }}
                  </p>

                  <div
                    v-if="getItemQuantity(item) > 0"
                    class="inline-flex h-8 items-center overflow-hidden rounded-lg border border-[#FFC8A8] bg-white text-[#1F2937]"
                  >
                    <button
                      class="grid size-8 place-items-center text-[#FF7A45] active:bg-[#FFF1E8]"
                      type="button"
                      aria-label="减少数量"
                      @click="removeItem(item)"
                    >
                      <Minus :size="15" />
                    </button>
                    <span class="grid h-8 min-w-8 place-items-center px-1 text-xs font-black">
                      {{ getItemQuantity(item) }}
                    </span>
                    <button
                      class="grid size-8 place-items-center text-[#FF7A45] active:bg-[#FFF1E8]"
                      type="button"
                      aria-label="增加数量"
                      @click="addItem(item)"
                    >
                      <Plus :size="15" />
                    </button>
                  </div>

                  <button
                    v-else
                    class="grid size-8 place-items-center rounded-lg bg-[#FF7A45] text-white shadow-[0_8px_18px_rgba(255,122,69,0.28)] disabled:bg-[#D1D5DB] disabled:shadow-none"
                    type="button"
                    :disabled="!canOrderItem(item)"
                    aria-label="加入点单"
                    @click="addItem(item)"
                  >
                    <Plus :size="18" />
                  </button>
                </div>
              </div>

              <p
                v-if="item.description_translated || item.description_original"
                class="mt-2 text-xs font-semibold leading-5 text-[#667085]"
              >
                {{ item.description_translated || item.description_original }}
              </p>

              <div class="mt-3 flex flex-wrap gap-1.5">
                <span
                  class="rounded-lg border px-2 py-1 text-[10px] font-black"
                  :class="availabilityClass(item)"
                >
                  {{ formatAvailability(item) }}
                </span>
                <span
                  v-for="tag in item.tags?.slice(0, 3)"
                  :key="tag"
                  class="rounded-lg border border-[#DCECF8] bg-white px-2 py-1 text-[10px] font-black text-[#4C7CA3]"
                >
                  {{ tag }}
                </span>
              </div>

              <p
                v-if="translatedAllergens(item).length"
                class="mt-2 text-[11px] font-semibold leading-4 text-[#B95048]"
              >
                过敏原：{{ translatedAllergens(item).join('、') }}
              </p>

              <div class="mt-3 rounded-lg border border-[#EFDCCC] bg-white p-2">
                <div class="flex items-center justify-between gap-2">
                  <span
                    class="inline-flex items-center gap-1 text-[11px] font-black text-[#667085]"
                  >
                    <Sparkles :size="13" />
                    综合置信度
                  </span>
                  <span class="text-xs font-black text-[#1F2937]">{{
                    confidencePercent(item.confidence)
                  }}</span>
                </div>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="entry in confidenceEntries(item.confidence)"
                    :key="entry.key"
                    class="rounded-lg bg-[#FFF8EF] px-2 py-1 text-[10px] font-black text-[#667085]"
                  >
                    {{ entry.label }} {{ entry.value }}
                  </span>
                </div>
              </div>
            </article>

            <div
              v-if="!filteredItems.length"
              class="rounded-lg border border-[#DCECF8] bg-white p-4 text-center text-sm font-black text-[#667085]"
            >
              {{ hasActiveMenuFilters ? '没有符合筛选的菜品' : '这个分类下暂时没有识别到菜品' }}
            </div>
          </div>
        </div>
      </section>

      <div
        class="sticky bottom-[88px] z-10 rounded-lg border border-[#EFDCCC] bg-white/92 p-3 shadow-[0_12px_30px_rgba(15,23,42,0.14)] backdrop-blur"
      >
        <div class="flex items-center gap-2">
          <div
            class="grid size-11 shrink-0 place-items-center rounded-lg bg-[#FFF1E8] text-[#FF7A45]"
          >
            <ClipboardList :size="22" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-black leading-5 text-[#1F2937]">已准备好点单</p>
            <p class="truncate text-xs font-semibold text-[#667085]">
              {{
                hasOrderItems
                  ? `已选 ${orderItemCount} 份`
                  : `当前分类 ${filteredItems.length} 道菜`
              }}
            </p>
          </div>
          <div class="w-[68px] shrink-0 text-right">
            <p class="text-[10px] font-black leading-4 text-[#667085]">总计</p>
            <p class="truncate text-base font-black leading-5 text-[#FF7A45]">
              {{ orderTotalLabel }}
            </p>
          </div>
          <button
            class="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-[#FF7A45] px-3 py-3 text-sm font-black text-white disabled:bg-[#D1D5DB]"
            type="button"
            :disabled="!hasOrderItems"
            @click="openOrderNote"
          >
            <ShoppingBag :size="17" />
            去下单
          </button>
        </div>
      </div>

      <Teleport to="body">
        <div
          v-if="isOrderNoteOpen"
          class="fixed inset-0 z-50 flex items-end justify-center bg-black/42 px-0"
          role="dialog"
          aria-modal="true"
          aria-labelledby="order-note-title"
          @click.self="closeOrderNote"
        >
          <section
            class="safe-bottom w-full max-w-[430px] rounded-t-lg border border-[#EFDCCC] bg-white shadow-[0_-18px_44px_rgba(15,23,42,0.2)]"
          >
            <header class="border-b border-[#F3E3D6] p-4">
              <div class="flex items-start gap-3">
                <div class="tm-icon-tile bg-[#FFF1E8] text-[#FF7A45]">
                  <MessageSquareText :size="22" />
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-black text-[#667085]">订单备注</p>
                  <h2
                    id="order-note-title"
                    class="mt-1 text-xl font-black leading-6 text-[#1F2937]"
                  >
                    去下单
                  </h2>
                  <p class="mt-2 text-sm font-semibold leading-5 text-[#667085]">
                    已选 {{ orderItemCount }} 份 · {{ orderTotalLabel }}
                  </p>
                </div>
                <button
                  class="grid size-9 shrink-0 place-items-center rounded-lg border border-[#EFDCCC] bg-white text-[#667085]"
                  type="button"
                  aria-label="关闭备注"
                  :disabled="isGeneratingOrder"
                  @click="closeOrderNote"
                >
                  <X :size="18" />
                </button>
              </div>
            </header>

            <div class="max-h-[68dvh] overflow-y-auto p-4">
              <div class="rounded-lg border border-[#F3E3D6] bg-[#FFFAF4] p-3">
                <div
                  v-for="line in selectedOrderLines"
                  :key="line.item.id"
                  class="flex items-start justify-between gap-3 border-b border-[#F3E3D6] py-2 first:pt-0 last:border-b-0 last:pb-0"
                >
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-black leading-5 text-[#1F2937]">
                      {{ line.item.name_translated || line.item.name_original || '未命名菜品' }}
                    </p>
                    <p class="mt-0.5 text-xs font-semibold text-[#667085]">
                      {{ formatPrice(line.item.price) }}
                    </p>
                  </div>
                  <p class="shrink-0 text-sm font-black text-[#FF7A45]">x{{ line.quantity }}</p>
                </div>
              </div>

              <div class="mt-4">
                <div class="mb-2 flex items-center justify-between gap-2">
                  <p class="text-sm font-black text-[#1F2937]">选择点菜单语言</p>
                  <span class="text-[11px] font-black text-[#B95048]">必选</span>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <button
                    v-for="language in ORDER_LANGUAGE_OPTIONS"
                    :key="language.code"
                    class="rounded-lg border px-3 py-2 text-left text-xs font-black leading-4 transition"
                    :class="
                      selectedOrderLanguage === language.code
                        ? 'border-[#FF7A45] bg-[#FFF1E8] text-[#BA5A32]'
                        : 'border-[#EFDCCC] bg-white text-[#667085]'
                    "
                    type="button"
                    :aria-pressed="selectedOrderLanguage === language.code"
                    @click="selectOrderLanguage(language.code)"
                  >
                    {{ language.label }}
                  </button>
                </div>
                <p
                  v-if="!selectedOrderLanguage"
                  class="mt-2 text-[11px] font-semibold leading-4 text-[#B95048]"
                >
                  请选择生成给店员看的语言。
                </p>
              </div>

              <div class="mt-4">
                <div class="mb-2 flex items-center justify-between gap-2">
                  <label class="text-sm font-black text-[#1F2937]" for="order-remark">备注</label>
                  <button
                    class="rounded-lg border border-[#EFDCCC] bg-white px-2.5 py-1 text-xs font-black text-[#667085] disabled:opacity-40"
                    type="button"
                    :disabled="!orderRemark"
                    @click="clearOrderRemark"
                  >
                    清空
                  </button>
                </div>
                <textarea
                  id="order-remark"
                  v-model="orderRemark"
                  class="min-h-28 w-full resize-none rounded-lg border border-[#EFDCCC] bg-white px-3 py-3 text-sm font-semibold leading-5 text-[#1F2937] outline-none focus:border-[#FF7A45]"
                  maxlength="160"
                  placeholder="例如：不要香菜、少辣、对花生过敏"
                />
                <p class="mt-1 text-right text-[11px] font-semibold text-[#98A2B3]">
                  {{ orderRemark.length }}/160
                </p>
              </div>

              <div class="mt-3 flex flex-wrap gap-2">
                <button
                  v-for="note in ORDER_NOTE_PRESETS"
                  :key="note"
                  class="rounded-lg border border-[#FFD8D3] bg-[#FFF2F0] px-3 py-2 text-xs font-black text-[#B95048]"
                  type="button"
                  @click="appendOrderNotePreset(note)"
                >
                  {{ note }}
                </button>
              </div>

              <p
                v-if="orderGenerationError"
                class="mt-4 rounded-lg border border-[#FFD8D3] bg-[#FFF2F0] px-3 py-2 text-xs font-black leading-5 text-[#B95048]"
              >
                {{ orderGenerationError }}
              </p>

              <section
                v-if="generatedOrderMenu"
                class="mt-4 rounded-lg border border-[#CBE5D8] bg-[#F1FAF6] p-3"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="text-xs font-black text-[#4F8D74]">AI 点菜单</p>
                    <h3 class="mt-1 text-base font-black leading-5 text-[#1F2937]">
                      {{ generatedOrderMenu.order.title }}
                    </h3>
                    <p
                      v-if="selectedOrderLanguageOption"
                      class="mt-1 text-xs font-semibold text-[#667085]"
                    >
                      {{ selectedOrderLanguageOption.label }}
                    </p>
                  </div>
                  <p class="shrink-0 text-base font-black text-[#FF7A45]">
                    {{ generatedOrderMenu.total.display_text }}
                  </p>
                </div>

                <div class="mt-3 rounded-lg border border-[#CBE5D8] bg-white p-3">
                  <p class="text-xs font-black text-[#667085]">给店员看</p>
                  <p class="mt-1 whitespace-pre-wrap text-sm font-black leading-6 text-[#1F2937]">
                    {{ generatedOrderMenu.local_language_order_text }}
                  </p>
                </div>

                <div class="mt-3 space-y-2">
                  <div
                    v-for="item in generatedOrderMenu.items"
                    :key="item.id"
                    class="rounded-lg border border-[#DCECF8] bg-white px-3 py-2"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0 flex-1">
                        <p class="truncate text-sm font-black leading-5 text-[#1F2937]">
                          {{ item.name }}
                        </p>
                        <p
                          v-if="item.original_name"
                          class="mt-0.5 truncate text-xs font-semibold text-[#667085]"
                        >
                          {{ item.original_name }}
                        </p>
                        <p
                          v-if="item.item_note"
                          class="mt-1 text-xs font-semibold leading-4 text-[#B95048]"
                        >
                          {{ item.item_note }}
                        </p>
                      </div>
                      <div class="shrink-0 text-right">
                        <p class="text-sm font-black text-[#FF7A45]">x{{ item.quantity }}</p>
                        <p class="mt-0.5 text-xs font-semibold text-[#667085]">
                          {{ item.subtotal.display_text }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <p class="mt-3 text-xs font-semibold leading-5 text-[#667085]">
                  {{ generatedOrderMenu.user_language_summary }}
                </p>

                <div
                  v-if="generatedOrderMenu.allergen_warnings.length"
                  class="mt-3 rounded-lg border border-[#FFD8D3] bg-white p-3"
                >
                  <p class="text-xs font-black text-[#B95048]">过敏提醒</p>
                  <ul class="mt-1 space-y-1 text-xs font-semibold leading-5 text-[#B95048]">
                    <li v-for="warning in generatedOrderMenu.allergen_warnings" :key="warning">
                      {{ warning }}
                    </li>
                  </ul>
                </div>
              </section>
            </div>

            <footer class="border-t border-[#F3E3D6] p-4">
              <div class="mb-3 flex items-center justify-between gap-3">
                <span class="text-sm font-black text-[#667085]">总计</span>
                <span class="text-xl font-black text-[#FF7A45]">{{ orderTotalLabel }}</span>
              </div>
              <button
                class="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#FF7A45] px-4 py-3 text-sm font-black text-white"
                type="button"
                :disabled="isGeneratingOrder"
                @click="submitOrder"
              >
                <Check :size="17" />
                {{
                  isGeneratingOrder
                    ? '正在生成点菜单...'
                    : generatedOrderMenu
                      ? '重新生成点菜单'
                      : '确认下单'
                }}
              </button>
            </footer>
          </section>
        </div>
      </Teleport>
    </template>
  </section>
</template>
