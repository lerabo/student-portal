<script setup>
import { reactive, ref } from 'vue'
import { ApiError, request } from '../api.js'

const props = defineProps({
  groupId: { type: Number, required: true },
})
const emit = defineEmits(['created'])

const form = reactive({ last_name: '', first_name: '' })
const errors = ref({})
const saving = ref(false)

async function submit() {
  saving.value = true
  errors.value = {}
  try {
    const student = await request('students/', {
      method: 'POST',
      body: { ...form, group: props.groupId },
    })
    emit('created', student)
    Object.assign(form, { last_name: '', first_name: '' })
  } catch (e) {
    errors.value =
      e instanceof ApiError && e.status === 400
        ? e.data
        : { detail: e.data?.detail ?? 'Не вдалося додати студента' }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <h2>Новий студент</h2>
    <label>Прізвище <input v-model.trim="form.last_name" required /></label>
    <span v-if="errors.last_name" class="error">{{ errors.last_name[0] }}</span>
    <label>Ім’я <input v-model.trim="form.first_name" required /></label>
    <span v-if="errors.first_name" class="error">{{ errors.first_name[0] }}</span>
    <p v-if="errors.detail" class="error">{{ errors.detail }}</p>
    <button type="submit" :disabled="saving">Додати</button>
  </form>
</template>

<style scoped>
.form {
  display: grid;
  gap: 0.4rem;
  max-width: 24rem;
  margin-top: 1.5rem;
}
h2 {
  margin: 0;
  font-size: 1.2rem;
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
