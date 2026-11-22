import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../App.vue'
import { KOVAL, reply } from './fixtures.js'

const TEACHER = ['add_grade', 'view_grade', 'view_student']
const DEAN = ['add_student', 'change_student', 'delete_student', 'view_student']

// «Сервер»: відповідь за методом і адресою запиту; невідоме - 404
function server(permissions, extra = {}) {
  const routes = {
    'GET /api/me/': [200, { username: 'user', permissions }],
    'GET /api/students/': [200, { count: 1, next: null, results: [KOVAL] }],
    ...extra,
  }
  return vi.fn(async (url, options = {}) => {
    const [status, data] = routes[`${options.method ?? 'GET'} ${url}`] ?? [404, {}]
    return reply(status, data)
  })
}

const labels = (wrapper) => wrapper.findAll('button').map((b) => b.text())

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('викладач бачить форму оцінки, але не видалення і не нового студента', async () => {
    vi.stubGlobal('fetch', server(TEACHER))
    const wrapper = mount(App)
    await flushPromises()

    expect(wrapper.text()).toContain('Ви увійшли як user')
    expect(labels(wrapper)).not.toContain('Видалити')
    expect(wrapper.text()).not.toContain('Новий студент')
    await wrapper.find('td button').trigger('click')
    expect(wrapper.text()).toContain('Нова оцінка')
  })

  it('після оцінки картка й таблиця показують свіжий середній бал з сервера', async () => {
    const fresh = { ...KOVAL, average: 90.3 }
    const grade = { id: 9, student: 1, course: 'Git', score: 88, ects: 'B' }
    vi.stubGlobal(
      'fetch',
      server(TEACHER, {
        'POST /api/grades/': [201, grade],
        'GET /api/students/1/': [200, fresh],
      }),
    )
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.find('td button').trigger('click')

    const form = wrapper.find('form')
    await form.findAll('input')[0].setValue('Git')
    await form.findAll('input')[1].setValue('88')
    await form.trigger('submit')
    await flushPromises()

    expect(wrapper.find('[role="status"]').text()).toBe('Оцінку 88 (B) виставлено')
    expect(wrapper.text()).toContain('90,3')
  })

  it('деканат бачить видалення і нового студента, але не форму оцінки', async () => {
    vi.stubGlobal(
      'fetch',
      server(DEAN, { 'DELETE /api/students/1/': [204, null] }),
    )
    vi.stubGlobal('confirm', () => true)
    const wrapper = mount(App)
    await flushPromises()

    expect(wrapper.text()).toContain('Новий студент')
    await wrapper.find('td button').trigger('click')
    expect(wrapper.text()).not.toContain('Нова оцінка')

    const remove = wrapper.findAll('button').find((b) => b.text() === 'Видалити')
    await remove.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Нікого не знайдено')
    expect(wrapper.find('[role="status"]').text()).toBe('Студента Коваль Олена видалено')
  })

  it('анонім - запрошення увійти', async () => {
    vi.stubGlobal(
      'fetch',
      server([], {
        'GET /api/me/': [403, { detail: 'Реквізити перевірки достовірності не надані.' }],
      }),
    )
    const wrapper = mount(App)
    await flushPromises()

    expect(wrapper.text()).toContain('Увійдіть на сайт')
    expect(wrapper.find('a').attributes('href')).toBe('/accounts/login/?next=/')
  })

  it('пошук фільтрує таблицю, Esc очищає', async () => {
    vi.stubGlobal('fetch', server(TEACHER))
    const wrapper = mount(App)
    await flushPromises()
    const search = wrapper.find('input[type="search"]')

    await search.setValue('мельн')
    expect(wrapper.text()).toContain('Нікого не знайдено')
    await search.trigger('keyup', { key: 'Escape' })
    expect(wrapper.text()).toContain('Коваль Олена')
  })
})
