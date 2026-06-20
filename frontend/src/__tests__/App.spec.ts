import { describe, it, expect } from 'vitest'

import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import App from '../App.vue'
import router from '../router'

describe('App', () => {
  it('renders the TaberuMate home screen', async () => {
    Object.defineProperty(window, 'scrollTo', {
      value: () => undefined,
      writable: true,
    })

    await router.push('/')

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('TaberuMate')
    expect(wrapper.text()).toContain('拍菜单开始')
  })

  it('prompts before ordering when no menu photo exists', async () => {
    Object.defineProperty(window, 'scrollTo', {
      value: () => undefined,
      writable: true,
    })

    await router.push('/orders')

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('还没有拍摄菜单')
    expect(wrapper.text()).toContain('现在去拍摄吧！')
  })
})
