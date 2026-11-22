import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StudentTable from '../components/StudentTable.vue'
import { BOIKO, KOVAL, MELNYK } from './fixtures.js'

// <TransitionGroup> у тестах - заглушка, тому рядки шукаємо без tbody
const rows = (wrapper) => wrapper.findAll('tr').slice(1)

describe('StudentTable', () => {
  it('рядок на студента із середнім балом або рискою', () => {
    const wrapper = mount(StudentTable, { props: { students: [KOVAL, BOIKO] } })

    expect(rows(wrapper)).toHaveLength(2)
    expect(rows(wrapper)[0].text()).toContain('Коваль Олена')
    expect(rows(wrapper)[0].text()).toContain('91,5')
    expect(rows(wrapper)[1].findAll('td')[1].text()).toBe('-')
  })

  it('подія select з об’єктом студента і підсвічений вибраний рядок', async () => {
    const wrapper = mount(StudentTable, {
      props: { students: [KOVAL, MELNYK], selectedId: 2 },
    })

    await rows(wrapper)[0].find('button').trigger('click')
    expect(wrapper.emitted('select')).toEqual([[KOVAL]])
    expect(rows(wrapper)[1].classes()).toContain('selected')
  })

  it('слот actions отримує студента рядка', () => {
    const wrapper = mount(StudentTable, {
      props: { students: [KOVAL, MELNYK] },
      slots: { actions: '<template #actions="{ student }">id {{ student.id }}</template>' },
    })

    expect(rows(wrapper).map((r) => r.findAll('td')[2].text())).toEqual(['id 1', 'id 2'])
  })
})
