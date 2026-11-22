import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import StudentForm from '../components/StudentForm.vue'
import { reply } from './fixtures.js'

async function fill(wrapper, lastName, firstName) {
  const [last, first] = wrapper.findAll('input')
  await last.setValue(lastName)
  await first.setValue(firstName)
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('StudentForm', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('додає студента в групу і очищає форму', async () => {
    const student = { id: 6, last_name: 'Ткачук', first_name: 'Софія', group: 1, average: null, grades: [] }
    const fetch = vi.fn(async () => reply(201, student))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(StudentForm, { props: { groupId: 1 } })

    await fill(wrapper, ' Ткачук ', 'Софія')

    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      last_name: 'Ткачук',
      first_name: 'Софія',
      group: 1,
    })
    expect(wrapper.emitted('created')).toEqual([[student]])
    expect(wrapper.findAll('input').map((i) => i.element.value)).toEqual(['', ''])
  })

  it('помилка 400 - біля поля, введене лишається', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => reply(400, { last_name: ['Це поле не може бути порожнім.'] })),
    )
    const wrapper = mount(StudentForm, { props: { groupId: 1 } })

    await fill(wrapper, '   ', 'Софія')

    expect(wrapper.find('.error').text()).toBe('Це поле не може бути порожнім.')
    expect(wrapper.findAll('input')[1].element.value).toBe('Софія')
    expect(wrapper.emitted('created')).toBeUndefined()
  })
})
