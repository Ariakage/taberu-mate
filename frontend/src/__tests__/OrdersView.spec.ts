import { afterEach, describe, expect, it, vi } from 'vitest'

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

import OrdersView from '@/views/OrdersView.vue'
import { useMenuScanStore } from '@/stores/menuScan'

const { generateOrderMenuMock } = vi.hoisted(() => ({
  generateOrderMenuMock: vi.fn(),
}))

vi.mock('@/services/orderAssistant', () => ({
  generateOrderMenu: generateOrderMenuMock,
  getOrderAssistantErrorMessage: (error: unknown) =>
    error instanceof Error ? error.message : 'AI 点菜单生成失败，请稍后再试',
}))

describe('OrdersView', () => {
  afterEach(() => {
    generateOrderMenuMock.mockReset()
    document.body.innerHTML = ''
  })

  it('opens an order remark sheet before confirming an order', async () => {
    generateOrderMenuMock.mockResolvedValue({
      order: {
        title: '点菜单',
        target_language: 'zh-CN',
        currency: 'JPY',
      },
      items: [
        {
          id: 'item_mapo',
          name: '麻婆豆腐',
          original_name: '麻婆豆腐',
          quantity: 1,
          unit_price: {
            amount: 900,
            currency: 'JPY',
            raw_text: '900円',
          },
          subtotal: {
            amount: 900,
            currency: 'JPY',
            display_text: '¥900',
          },
          item_note: '少辣',
        },
      ],
      customer_note: '少辣',
      restaurant_note: '请做成少辣。',
      local_language_order_text: '麻婆豆腐 1份。请做成少辣。',
      user_language_summary: '已选择 1 份麻婆豆腐。',
      allergen_warnings: [],
      total: {
        amount: 900,
        currency: 'JPY',
        display_text: '¥900',
      },
    })

    const pinia = createPinia()
    setActivePinia(pinia)

    const menuScanStore = useMenuScanStore()
    menuScanStore.result = {
      menu: {
        currency: 'JPY',
        target_language: 'zh-CN',
      },
      categories: [
        {
          id: 'cat_main',
          name_translated: '主菜',
          sort_order: 1,
        },
      ],
      items: [
        {
          id: 'item_mapo',
          primary_category_id: 'cat_main',
          category_ids: ['cat_main'],
          name_original: '麻婆豆腐',
          name_translated: '麻婆豆腐',
          price: {
            amount: 900,
            currency: 'JPY',
            raw_text: '900円',
          },
          allergens: ['soybeans'],
          taste_profile: {
            spicy_level: 3,
            sweet_level: 1,
          },
          availability: {
            status: 'available',
          },
        },
        {
          id: 'item_soup',
          primary_category_id: 'cat_main',
          category_ids: ['cat_main'],
          name_original: '野菜スープ',
          name_translated: '蔬菜汤',
          price: {
            amount: 500,
            currency: 'JPY',
            raw_text: '500円',
          },
          allergens: [],
          taste_profile: {
            spicy_level: 0,
            richness_level: 1,
            salty_level: 1,
          },
          availability: {
            status: 'available',
          },
        },
      ],
    }

    const wrapper = mount(OrdersView, {
      attachTo: document.body,
      global: {
        plugins: [pinia],
      },
    })

    expect(wrapper.text()).toContain('筛选')
    expect(wrapper.text()).toContain('辣味')
    expect(wrapper.text()).toContain('大豆')
    expect(wrapper.text()).toContain('蔬菜汤')

    const spicyFilter = wrapper.findAll('button').find((button) => button.text() === '辣味')
    expect(spicyFilter).toBeTruthy()
    await spicyFilter?.trigger('click')
    expect(wrapper.text()).toContain('麻婆豆腐')
    expect(wrapper.text()).not.toContain('蔬菜汤')

    const clearFilter = wrapper.findAll('button').find((button) => button.text() === '清空')
    expect(clearFilter).toBeTruthy()
    await clearFilter?.trigger('click')
    expect(wrapper.text()).toContain('蔬菜汤')

    const soybeanFilter = wrapper.findAll('button').find((button) => button.text() === '大豆')
    expect(soybeanFilter).toBeTruthy()
    await soybeanFilter?.trigger('click')
    expect(wrapper.text()).toContain('蔬菜汤')
    expect(wrapper.text()).not.toContain('麻婆豆腐')

    const clearAvoidanceFilter = wrapper.findAll('button').find((button) => button.text() === '清空')
    expect(clearAvoidanceFilter).toBeTruthy()
    await clearAvoidanceFilter?.trigger('click')

    const addButtons = wrapper.findAll('button[aria-label="加入点单"]')
    expect(addButtons.length).toBeGreaterThan(0)
    await addButtons[0]?.trigger('click')
    expect(wrapper.text()).toContain('已选 1 份')
    expect(wrapper.text()).toContain('¥900')

    const orderButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('去下单'))
    expect(orderButton).toBeTruthy()
    await orderButton?.trigger('click')

    expect(document.body.textContent).toContain('订单备注')
    expect(document.body.textContent).toContain('已选 1 份 · ¥900')
    expect(document.body.textContent).toContain('中文简体')
    expect(document.body.textContent).toContain('香港粤语')
    expect(document.body.textContent).toContain('台湾客家话')
    expect(document.body.textContent).toContain('英文 UK')
    expect(document.body.textContent).toContain('英文 US')
    expect(document.body.textContent).toContain('日语')
    expect(document.body.textContent).toContain('韩语')
    expect(document.body.textContent).toContain('泰国语言')

    const presetButton = [...document.body.querySelectorAll('button')].find((button) =>
      button.textContent?.includes('少辣'),
    )
    expect(presetButton).toBeTruthy()
    presetButton?.click()
    await nextTick()

    const textarea = document.querySelector<HTMLTextAreaElement>('#order-remark')
    expect(textarea?.value).toBe('少辣')

    const confirmButton = [...document.body.querySelectorAll('button')].find((button) =>
      button.textContent?.includes('确认下单'),
    )
    expect(confirmButton).toBeTruthy()
    confirmButton?.click()
    await nextTick()

    expect(generateOrderMenuMock).not.toHaveBeenCalled()
    expect(document.body.textContent).toContain('请选择点菜单语言')

    const languageButton = [...document.body.querySelectorAll('button')].find((button) =>
      button.textContent?.includes('日语'),
    )
    expect(languageButton).toBeTruthy()
    languageButton?.click()
    await nextTick()

    confirmButton?.click()
    await nextTick()
    await nextTick()

    expect(generateOrderMenuMock).toHaveBeenCalledWith(
      expect.objectContaining({
        target_language: 'Japanese (ja)',
        target_language_code: 'ja',
        customer_remark: '少辣',
        total_amount: 900,
        items: [
          expect.objectContaining({
            id: 'item_mapo',
            quantity: 1,
          }),
        ],
      }),
    )
    const generatedOrderInput = generateOrderMenuMock.mock.calls[0]?.[0]
    expect(generatedOrderInput?.items[0]).not.toHaveProperty('allergens')
    expect(document.body.textContent).toContain('AI 点菜单')
    expect(document.body.textContent).toContain('麻婆豆腐 1份。请做成少辣。')
    expect(document.body.textContent).not.toContain('JSON')
  })
})
