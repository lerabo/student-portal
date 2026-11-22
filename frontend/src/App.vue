<script setup>
import { computed, onMounted, ref } from 'vue'
import { request } from './api.js'
import GradeForm from './components/GradeForm.vue'
import StudentCard from './components/StudentCard.vue'
import StudentForm from './components/StudentForm.vue'
import StudentTable from './components/StudentTable.vue'

const me = ref(null)
const students = ref([])
const loading = ref(true)
const error = ref('')
const query = ref('')
const selectedId = ref(null)
const message = ref('')

async function load() {
  try {
    const [user, page] = await Promise.all([request('me/'), request('students/')])
    me.value = user
    students.value = page.results
  } catch (e) {
    error.value = e.status === 403 ? 'Увійдіть на сайт' : 'Не вдалося завантажити список'
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Права перевіряє сервер; can() лише ховає дії, недоступні ролі
function can(permission) {
  return me.value?.permissions.includes(permission) ?? false
}

const found = computed(() => {
  const q = query.value.toLowerCase()
  return students.value.filter((s) =>
    `${s.last_name} ${s.first_name}`.toLowerCase().includes(q),
  )
})

// Зберігається id, а не об'єкт: після оновлення списку картка бере свіжі дані
const selected = computed(
  () => students.value.find((s) => s.id === selectedId.value) ?? null,
)
const groupId = computed(() => students.value[0]?.group ?? null)

async function gradeCreated(grade) {
  // Середній бал рахує сервер: перечитуємо студента і замінюємо його в списку
  const fresh = await request(`students/${grade.student}/`)
  students.value = students.value.map((s) => (s.id === fresh.id ? fresh : s))
  message.value = `Оцінку ${grade.score} (${grade.ects}) виставлено`
}

function studentCreated(student) {
  students.value = [...students.value, student]
  message.value = `Студента ${student.last_name} ${student.first_name} додано`
}

async function remove(student) {
  const name = `${student.last_name} ${student.first_name}`
  if (!confirm(`Видалити студента ${name}?`)) return
  try {
    await request(`students/${student.id}/`, { method: 'DELETE' })
    students.value = students.value.filter((s) => s.id !== student.id)
    if (selectedId.value === student.id) selectedId.value = null
    message.value = `Студента ${name} видалено`
  } catch (e) {
    message.value = e.data?.detail ?? 'Не вдалося видалити студента'
  }
}
</script>

<template>
  <h1>Студенти</h1>
  <p v-if="loading">Завантаження…</p>
  <p v-else-if="error" class="error">
    {{ error }}: <a href="/accounts/login/?next=/">сторінка входу</a>
  </p>
  <template v-else>
    <p class="user">Ви увійшли як {{ me.username }}</p>
    <p role="status" class="message">{{ message }}</p>

    <label class="search">
      Пошук
      <input
        v-model.trim="query"
        type="search"
        placeholder="Прізвище або ім’я"
        @keyup.esc="query = ''"
      />
    </label>

    <div class="layout">
      <div>
        <StudentTable
          v-if="found.length"
          :students="found"
          :selected-id="selectedId"
          @select="selectedId = $event.id"
        >
          <template #actions="{ student }">
            <button
              v-if="can('delete_student')"
              type="button"
              class="danger"
              @click="remove(student)"
            >
              Видалити
            </button>
          </template>
        </StudentTable>
        <p v-else>Нікого не знайдено</p>

        <StudentForm
          v-if="can('add_student') && groupId !== null"
          :group-id="groupId"
          @created="studentCreated"
        />
      </div>

      <Transition name="card" mode="out-in">
        <StudentCard
          v-if="selected"
          :key="selected.id"
          :student="selected"
          @close="selectedId = null"
        >
          <GradeForm
            v-if="can('add_grade')"
            :student-id="selected.id"
            @created="gradeCreated"
          />
        </StudentCard>
      </Transition>
    </div>
  </template>
</template>

<style>
#app {
  font-family: system-ui, sans-serif;
  max-width: 64rem;
}
.error {
  color: #b00020;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}
@media (max-width: 48rem) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>

<style scoped>
.search {
  display: block;
  margin-bottom: 1rem;
}
.search input {
  margin-left: 0.5rem;
  padding: 0.25rem 0.5rem;
}
.message:empty {
  display: none;
}
.message {
  padding: 0.5rem 0.75rem;
  background: #e8f5e9;
  border-radius: 4px;
}
.danger {
  color: #b00020;
}
.card-enter-active,
.card-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.card-enter-from,
.card-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
@media (prefers-reduced-motion: reduce) {
  .card-enter-active,
  .card-leave-active {
    transition: none;
  }
}
</style>
