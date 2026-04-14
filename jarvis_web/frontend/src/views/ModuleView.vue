<template>
  <section class="mx-auto max-w-5xl space-y-4">
    <header>
      <h1 class="text-2xl font-semibold">{{ title }}</h1>
      <p class="text-sm text-slate-600">Cadastro e consulta de {{ title.toLowerCase() }}.</p>
    </header>

    <div class="rounded-xl border bg-white p-4">
      <form class="grid gap-2 md:grid-cols-4" @submit.prevent="save">
        <input v-for="field in fields" :key="field" v-model="form[field]" :placeholder="field" class="rounded border px-3 py-2 text-sm" required />
        <button class="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 md:col-span-1">
          {{ editingId ? 'Atualizar' : 'Adicionar' }}
        </button>
      </form>
    </div>

    <div class="overflow-hidden rounded-xl border bg-white">
      <table class="min-w-full text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-3 py-2 text-left">ID</th>
            <th v-for="field in fields" :key="field" class="px-3 py-2 text-left">{{ field }}</th>
            <th class="px-3 py-2">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" class="border-t">
            <td class="px-3 py-2">{{ item.id }}</td>
            <td v-for="field in fields" :key="field" class="px-3 py-2">{{ item[field] }}</td>
            <td class="space-x-2 px-3 py-2 text-right">
              <button class="rounded bg-amber-500 px-2 py-1 text-white" @click="edit(item)">Editar</button>
              <button class="rounded bg-red-600 px-2 py-1 text-white" @click="remove(item.id)">Excluir</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { moduleApi } from '../services/api'

const props = defineProps({
  moduleKey: { type: String, required: true },
  title: { type: String, required: true },
})

const mapFields = {
  tasks: ['title', 'description', 'due_date', 'completed'],
  appointments: ['title', 'location', 'start_time', 'end_time'],
  notes: ['title', 'content'],
  expenses: ['description', 'amount', 'category', 'expense_date'],
  reminders: ['message', 'remind_at', 'done'],
}

const fields = computed(() => mapFields[props.moduleKey] || [])
const items = ref([])
const form = reactive({})
const editingId = ref(null)

function resetForm() {
  fields.value.forEach((field) => {
    form[field] = ''
  })
  editingId.value = null
}

async function load() {
  const { data } = await moduleApi.list(props.moduleKey)
  items.value = data
}

async function save() {
  const payload = { ...form }
  if (props.moduleKey === 'tasks') payload.completed = payload.completed === true || payload.completed === 'true'
  if (props.moduleKey === 'reminders') payload.done = payload.done === true || payload.done === 'true'
  if (props.moduleKey === 'expenses') payload.amount = Number(payload.amount)

  if (editingId.value) {
    await moduleApi.update(props.moduleKey, editingId.value, payload)
  } else {
    await moduleApi.create(props.moduleKey, payload)
  }
  await load()
  resetForm()
}

function edit(item) {
  editingId.value = item.id
  fields.value.forEach((field) => {
    form[field] = item[field]
  })
}

async function remove(id) {
  await moduleApi.remove(props.moduleKey, id)
  await load()
}

onMounted(async () => {
  resetForm()
  await load()
})
</script>
