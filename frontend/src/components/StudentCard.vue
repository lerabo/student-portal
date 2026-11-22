<script setup>
import { formatAverage } from '../format.js'

defineProps({
  student: { type: Object, required: true },
})
const emit = defineEmits(['close'])
</script>

<template>
  <section class="card" aria-labelledby="card-title">
    <h2 id="card-title">{{ student.last_name }} {{ student.first_name }}</h2>
    <p>
      Середній бал: <strong>{{ formatAverage(student.average) }}</strong>
    </p>
    <table v-if="student.grades.length">
      <thead>
        <tr>
          <th scope="col">Дисципліна</th>
          <th scope="col">Бали</th>
          <th scope="col">ECTS</th>
          <th scope="col">Дата</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="grade in student.grades" :key="grade.id">
          <td>{{ grade.course }}</td>
          <td class="number">{{ grade.score }}</td>
          <td>{{ grade.ects }}</td>
          <td>{{ grade.graded_on }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">Оцінок ще немає</p>
    <slot />
    <button type="button" @click="emit('close')">Закрити</button>
  </section>
</template>

<style scoped>
.card {
  padding: 1rem 1.25rem;
  border: 1px solid #ccc;
  border-radius: 8px;
}
h2 {
  margin-top: 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}
th,
td {
  padding: 0.3rem 0.5rem;
  border-bottom: 1px solid #eee;
  text-align: left;
}
.number {
  text-align: right;
}
.empty {
  color: #777;
}
</style>
