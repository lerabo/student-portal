import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import GradeForm from '../components/GradeForm.vue'
import { reply } from './fixtures.js'

const today = new Date().toISOString().slice(0, 10)

async function fill(wrapper, course, score) {
  const [courseInput, scoreInput] = wrapper.findAll('input')
  await courseInput.setValue(course)
  await scoreInput.setValue(score)
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('GradeForm', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('надсилає оцінку з числом балів і повідомляє подією created', async () => {
    const grade = { id: 9, student: 4, course: 'Git', score: 88, graded_on: today, ects: 'B' }
    const fetch = vi.fn(async () => reply(201, grade))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(GradeForm, { props: { studentId: 4 } })

    await fill(wrapper, '  Git  ', '88')

    const [url, options] = fetch.mock.calls[0]
    expect(url).toBe('/api/grades/')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({
      course: 'Git',
      score: 88,
      graded_on: today,
      student: 4,
    })
    expect(wrapper.emitted('created')).toEqual([[grade]])
    expect(wrapper.findAll('input')[0].element.value).toBe('')
  })

  it('помилка 400 - біля поля, подія не надсилається', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => reply(400, { score: ['Переконайтеся, що це значення менше або дорівнює 100.'] })),
    )
    const wrapper = mount(GradeForm, { props: { studentId: 4 } })

    await fill(wrapper, 'Git', '101')

    expect(wrapper.find('.error').text()).toBe(
      'Переконайтеся, що це значення менше або дорівнює 100.',
    )
    expect(wrapper.emitted('created')).toBeUndefined()
  })
})
