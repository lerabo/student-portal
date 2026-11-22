// Студенти у формі відповіді DRF: список з оцінками і середнім балом
export const KOVAL = {
  id: 1,
  first_name: 'Олена',
  last_name: 'Коваль',
  group: 1,
  average: 91.5,
  grades: [
    { id: 1, student: 1, course: 'Python', score: 95, graded_on: '2026-10-01', ects: 'A' },
    { id: 2, student: 1, course: 'Бази даних', score: 88, graded_on: '2026-10-08', ects: 'B' },
  ],
}

export const MELNYK = {
  id: 2,
  first_name: 'Андрій',
  last_name: 'Мельник',
  group: 1,
  average: 61,
  grades: [
    { id: 3, student: 2, course: 'Python', score: 61, graded_on: '2026-10-01', ects: 'E' },
  ],
}

export const BOIKO = {
  id: 3,
  first_name: 'Ірина',
  last_name: 'Бойко',
  group: 1,
  average: null,
  grades: [],
}

// Відповідь fetch: ok, status і json(), як у справжнього Response
export function reply(status, data) {
  return { ok: status >= 200 && status < 300, status, json: async () => data }
}
