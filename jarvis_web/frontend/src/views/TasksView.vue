<template>
  <div class="space-y-4">
    <PageCard>
      <div class="mb-4">
        <h3 class="text-lg font-semibold text-slate-900">Tarefas</h3>
        <p class="text-sm text-slate-500">Gerencie tarefas simples e recorrentes.</p>
      </div>

      <FeedbackAlert :type="feedbackType" :message="feedbackMessage" />

      <form class="mt-3 grid gap-3 md:grid-cols-2" @submit.prevent="saveTask">
        <label class="space-y-1 text-sm md:col-span-2">
          <span class="font-medium text-slate-700">Título</span>
          <input
            v-model="form.title"
            required
            type="text"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring"
          />
        </label>

        <label class="space-y-1 text-sm md:col-span-2">
          <span class="font-medium text-slate-700">Descrição</span>
          <textarea
            v-model="form.description"
            rows="3"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring"
          ></textarea>
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium text-slate-700">Prioridade</span>
          <select v-model="form.priority" required class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring">
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium text-slate-700">Status</span>
          <select v-model="form.status" required class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring">
            <option value="pending">pending</option>
            <option value="in_progress">in_progress</option>
            <option value="done">done</option>
          </select>
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium text-slate-700">Data limite (simples)</span>
          <input
            v-model="form.due_date"
            :disabled="form.isRecurring"
            type="date"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 disabled:bg-slate-100 focus:ring"
          />
        </label>

        <label class="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
          <input v-model="form.isRecurring" type="checkbox" class="h-4 w-4 rounded border-slate-300" @change="handleRecurringToggle" />
          Tarefa recorrente
        </label>

        <template v-if="form.isRecurring">
          <div class="md:col-span-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p class="mb-3 text-sm font-medium text-slate-800">Configuração de recorrência</p>
            <div class="grid gap-3 md:grid-cols-2">
              <label class="space-y-1 text-sm">
                <span class="font-medium text-slate-700">Data inicial</span>
                <input v-model="form.start_date" required type="date" class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring" />
              </label>

              <label class="space-y-1 text-sm">
                <span class="font-medium text-slate-700">Data final</span>
                <input v-model="form.end_date" required type="date" class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring" />
              </label>

              <label class="space-y-1 text-sm md:col-span-2">
                <span class="font-medium text-slate-700">Padrão de recorrência</span>
                <select v-model="form.recurrence_pattern" class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring">
                  <option value="daily">daily</option>
                  <option value="weekly">weekly</option>
                  <option value="monthly">monthly</option>
                  <option value="interval">interval</option>
                </select>
              </label>

              <div v-if="form.recurrence_pattern === 'weekly'" class="space-y-2 text-sm md:col-span-2">
                <span class="font-medium text-slate-700">Dias da semana</span>
                <div class="flex flex-wrap gap-3">
                  <label v-for="day in weekdayOptions" :key="day.value" class="inline-flex items-center gap-2 text-slate-700">
                    <input
                      :checked="form.recurrence_meta.weekdays.includes(day.value)"
                      type="checkbox"
                      class="h-4 w-4 rounded border-slate-300"
                      @change="toggleWeeklyDay(day.value)"
                    />
                    {{ day.label }}
                  </label>
                </div>
              </div>

              <label v-if="form.recurrence_pattern === 'monthly'" class="space-y-1 text-sm md:col-span-2">
                <span class="font-medium text-slate-700">Dia do mês</span>
                <input
                  v-model.number="form.recurrence_meta.day_of_month"
                  min="1"
                  max="31"
                  type="number"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring"
                />
              </label>

              <label v-if="form.recurrence_pattern === 'interval'" class="space-y-1 text-sm md:col-span-2">
                <span class="font-medium text-slate-700">Intervalo em dias</span>
                <input
                  v-model.number="form.recurrence_meta.every_days"
                  min="1"
                  type="number"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring"
                />
              </label>
            </div>
          </div>
        </template>

        <div class="md:col-span-2 flex flex-wrap gap-2">
          <button class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" :disabled="loading">
            {{ editingId ? 'Salvar alterações' : 'Criar tarefa' }}
          </button>
          <button
            v-if="editingId"
            type="button"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            @click="resetForm"
          >
            Cancelar edição
          </button>
        </div>
      </form>
    </PageCard>

    <PageCard>
      <div v-if="loading" class="text-sm text-slate-500">Carregando...</div>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="border-b border-slate-200 bg-slate-50 text-left text-slate-600">
            <tr>
              <th class="px-3 py-2">ID</th>
              <th class="px-3 py-2">Título</th>
              <th class="px-3 py-2">Prioridade</th>
              <th class="px-3 py-2">Status</th>
              <th class="px-3 py-2">Data</th>
              <th class="px-3 py-2">Recorrência</th>
              <th class="px-3 py-2 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" class="border-b border-slate-100">
              <td class="px-3 py-2 text-slate-500">{{ item.id }}</td>
              <td class="px-3 py-2">
                <div class="flex items-center gap-2">
                  <span>{{ item.title }}</span>
                  <span v-if="item.is_recurring" class="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-semibold text-indigo-700">Recorrente</span>
                </div>
                <p v-if="item.is_recurring" class="text-xs text-slate-500">Pertence a uma recorrência.</p>
                <p v-if="item.is_recurring" class="text-xs text-slate-500">Grupo: {{ item.recurrence_group_id || '-' }}</p>
              </td>
              <td class="px-3 py-2">{{ item.priority }}</td>
              <td class="px-3 py-2">{{ item.status }}</td>
              <td class="px-3 py-2">{{ formatDate(item.due_date) }}</td>
              <td class="px-3 py-2">
                <span v-if="item.is_recurring" class="rounded-md border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">
                  {{ item.recurrence_pattern || 'recurring' }}
                </span>
                <span v-else class="text-slate-400">-</span>
              </td>
              <td class="px-3 py-2 text-right">
                <div class="inline-flex gap-2">
                  <button class="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium hover:bg-slate-100" @click="startEdit(item)">Editar</button>
                  <button class="rounded-md bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700" @click="removeTask(item.id)">Excluir</button>
                  <button
                    v-if="item.is_recurring"
                    disabled
                    title="Escopo de edição/exclusão (single/future/all) será habilitado em breve"
                    class="cursor-not-allowed rounded-md border border-dashed border-slate-300 px-2 py-1 text-xs text-slate-400"
                  >
                    Escopo (em breve)
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!items.length">
              <td colspan="7" class="px-3 py-6 text-center text-slate-500">Nenhuma tarefa encontrada.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PageCard>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'

import PageCard from '../components/shared/PageCard.vue'
import FeedbackAlert from '../components/shared/FeedbackAlert.vue'
import { moduleApi, taskApi } from '../services/api'

const loading = ref(false)
const items = ref([])
const editingId = ref(null)
const feedbackType = ref('info')
const feedbackMessage = ref('')

const weekdayOptions = [
  { value: 'monday', label: 'Seg' },
  { value: 'tuesday', label: 'Ter' },
  { value: 'wednesday', label: 'Qua' },
  { value: 'thursday', label: 'Qui' },
  { value: 'friday', label: 'Sex' },
  { value: 'saturday', label: 'Sáb' },
  { value: 'sunday', label: 'Dom' },
]

const form = reactive({
  title: '',
  description: '',
  priority: 'medium',
  status: 'pending',
  due_date: '',
  isRecurring: false,
  start_date: '',
  end_date: '',
  recurrence_pattern: 'daily',
  recurrence_meta: {
    weekdays: [],
    day_of_month: 1,
    every_days: 1,
  },
})

function resetForm() {
  form.title = ''
  form.description = ''
  form.priority = 'medium'
  form.status = 'pending'
  form.due_date = ''
  form.isRecurring = false
  form.start_date = ''
  form.end_date = ''
  form.recurrence_pattern = 'daily'
  form.recurrence_meta.weekdays = []
  form.recurrence_meta.day_of_month = 1
  form.recurrence_meta.every_days = 1
  editingId.value = null
}

function handleRecurringToggle() {
  if (form.isRecurring) {
    form.due_date = ''
  }
}

function toggleWeeklyDay(day) {
  if (form.recurrence_meta.weekdays.includes(day)) {
    form.recurrence_meta.weekdays = form.recurrence_meta.weekdays.filter((item) => item !== day)
    return
  }
  form.recurrence_meta.weekdays = [...form.recurrence_meta.weekdays, day]
}

function buildSimplePayload() {
  return {
    title: form.title,
    description: form.description || null,
    priority: form.priority,
    status: form.status,
    due_date: form.due_date || null,
  }
}

function buildRecurringMeta() {
  if (form.recurrence_pattern === 'weekly') {
    return { weekdays: form.recurrence_meta.weekdays }
  }

  if (form.recurrence_pattern === 'monthly') {
    return { day_of_month: Number(form.recurrence_meta.day_of_month) }
  }

  if (form.recurrence_pattern === 'interval') {
    return { every_days: Number(form.recurrence_meta.every_days) }
  }

  return {}
}

function buildRecurringPayload() {
  return {
    title: form.title,
    description: form.description || null,
    priority: form.priority,
    status: form.status,
    start_date: form.start_date,
    end_date: form.end_date,
    recurrence_pattern: form.recurrence_pattern,
    recurrence_meta: buildRecurringMeta(),
  }
}

function validateRecurringForm() {
  if (!form.start_date || !form.end_date) {
    return 'Informe data inicial e data final da recorrência.'
  }

  if (form.recurrence_pattern === 'weekly' && !form.recurrence_meta.weekdays.length) {
    return 'Selecione ao menos um dia da semana para weekly.'
  }

  if (form.recurrence_pattern === 'monthly') {
    const day = Number(form.recurrence_meta.day_of_month)
    if (!Number.isInteger(day) || day < 1 || day > 31) {
      return 'Dia do mês inválido. Use um valor entre 1 e 31.'
    }
  }

  if (form.recurrence_pattern === 'interval') {
    const everyDays = Number(form.recurrence_meta.every_days)
    if (!Number.isInteger(everyDays) || everyDays < 1) {
      return 'Intervalo em dias deve ser maior que zero.'
    }
  }

  return null
}

function normalizeItemForEdit(item) {
  form.title = item.title || ''
  form.description = item.description || ''
  form.priority = item.priority || 'medium'
  form.status = item.status || 'pending'
  form.due_date = item.due_date || ''

  form.isRecurring = false
  form.start_date = ''
  form.end_date = ''
  form.recurrence_pattern = 'daily'
  form.recurrence_meta.weekdays = []
  form.recurrence_meta.day_of_month = 1
  form.recurrence_meta.every_days = 1
}

function startEdit(item) {
  editingId.value = item.id
  normalizeItemForEdit(item)
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

async function loadTasks() {
  loading.value = true
  feedbackMessage.value = ''

  try {
    const { data } = await moduleApi.list('tasks')
    items.value = data
  } catch (error) {
    feedbackType.value = 'error'
    feedbackMessage.value = error?.response?.data?.detail || 'Falha ao carregar tarefas.'
  } finally {
    loading.value = false
  }
}

async function saveTask() {
  loading.value = true
  feedbackMessage.value = ''

  try {
    if (editingId.value) {
      await moduleApi.update('tasks', editingId.value, buildSimplePayload())
      feedbackType.value = 'success'
      feedbackMessage.value = 'Tarefa atualizada com sucesso.'
    } else if (form.isRecurring) {
      const validationError = validateRecurringForm()
      if (validationError) {
        feedbackType.value = 'error'
        feedbackMessage.value = validationError
        return
      }

      await taskApi.createRecurring(buildRecurringPayload())
      feedbackType.value = 'success'
      feedbackMessage.value = 'Tarefas recorrentes criadas com sucesso.'
    } else {
      await taskApi.createSimple(buildSimplePayload())
      feedbackType.value = 'success'
      feedbackMessage.value = 'Tarefa criada com sucesso.'
    }

    await loadTasks()
    resetForm()
  } catch (error) {
    feedbackType.value = 'error'
    feedbackMessage.value = error?.response?.data?.detail || 'Erro ao salvar tarefa.'
  } finally {
    loading.value = false
  }
}

async function removeTask(taskId) {
  loading.value = true
  feedbackMessage.value = ''

  try {
    await moduleApi.remove('tasks', taskId)
    feedbackType.value = 'success'
    feedbackMessage.value = 'Tarefa excluída com sucesso.'
    await loadTasks()
  } catch (error) {
    feedbackType.value = 'error'
    feedbackMessage.value = error?.response?.data?.detail || 'Erro ao excluir tarefa.'
  } finally {
    loading.value = false
  }
}

loadTasks()
</script>
