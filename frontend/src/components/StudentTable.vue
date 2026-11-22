<script setup>
import { formatAverage } from '../format.js'

defineProps({
  students: { type: Array, required: true },
  selectedId: { type: Number, default: null },
})
const emit = defineEmits(['select'])
</script>

<template>
  <table>
    <thead>
      <tr>
        <th scope="col">Студент</th>
        <th scope="col">Середній бал</th>
        <th scope="col">Дії</th>
      </tr>
    </thead>
    <TransitionGroup name="row" tag="tbody">
      <tr
        v-for="student in students"
        :key="student.id"
        :class="{ selected: student.id === selectedId }"
      >
        <td>
          <button type="button" class="link" @click="emit('select', student)">
            {{ student.last_name }} {{ student.first_name }}
          </button>
        </td>
        <td class="number" :class="{ empty: student.average === null }">
          {{ formatAverage(student.average) }}
        </td>
        <td><slot name="actions" :student="student" /></td>
      </tr>
    </TransitionGroup>
  </table>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid #ddd;
  text-align: left;
}
.number {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.empty {
  color: #777;
}
.selected {
  background: #e3f2fd;
}
.link {
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  cursor: pointer;
  color: #0b5cad;
  text-decoration: underline;
}
.row-move,
.row-enter-active,
.row-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}
.row-enter-from,
.row-leave-to {
  opacity: 0;
  transform: translateX(-1rem);
}
.row-leave-active {
  position: absolute;
}
@media (prefers-reduced-motion: reduce) {
  .row-move,
  .row-enter-active,
  .row-leave-active {
    transition: none;
  }
}
</style>
