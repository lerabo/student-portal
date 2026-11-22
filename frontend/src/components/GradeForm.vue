<script setup>
import { reactive, ref } from 'vue'
import { ApiError, request } from '../api.js'

const props = defineProps({
  studentId: { type: Number, required: true },
})
const emit = defineEmits(['created'])

// Дата для <input type="date"> - рядок YYYY-MM-DD
const today = () => new Date().toISOString().slice(0, 10)

const form = reactive({ course: '', score: null, graded_on: today() })
const errors = ref({})
const saving = ref(false)

async function submit() {
  saving.value = true
  errors.value = {}
  try {
    const grade = await request('grades/', {
      method: 'POST',
      body: { ...form, student: props.studentId },
    })
    emit('created', grade)
    Object.assign(form, { course: '', score: null, graded_on: today() })
  } catch (e) {
    errors.value =
      e instanceof ApiError && e.status === 400
        ? e.data
        : { detail: e.data?.detail ?? 'Не вдалося зберегти оцінку' }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <h3>Нова оцінка</h3>
    <label>
      Дисципліна <input v-model.trim="form.course" required maxlength="100" />
    </label>
    <span v-if="errors.course" class="error">{{ errors.course[0] }}</span>
    <label>
      Бали
      <input v-model.number="form.score" type="number" min="0" max="100" required />
    </label>
    <span v-if="errors.score" class="error">{{ errors.score[0] }}</span>
    <label>Дата <input v-model="form.graded_on" type="date" required /></label>
    <span v-if="errors.graded_on" class="error">{{ errors.graded_on[0] }}</span>
    <p v-if="errors.non_field_errors" class="error">{{ errors.non_field_errors[0] }}</p>
    <p v-if="errors.detail" class="error">{{ errors.detail }}</p>
    <button type="submit" :disabled="saving">Виставити</button>
  </form>
</template>

<style scoped>
.form {
  display: grid;
  gap: 0.4rem;
  margin: 1rem 0;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
}
h3 {
  margin: 0;
}
label {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}
.error {
  color: #b00020;
  font-size: 0.9em;
}
button {
  justify-self: start;
}
</style>
