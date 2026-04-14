<template>
  <section class="mx-auto max-w-4xl space-y-4">
    <header>
      <h1 class="text-2xl font-semibold">Assistente pessoal</h1>
      <p class="text-sm text-slate-600">Converse com o Jarvis e salve histórico local.</p>
    </header>

    <div class="rounded-xl border bg-white p-4">
      <div class="mb-4 max-h-[60vh] space-y-3 overflow-y-auto pr-2">
        <div v-for="msg in messages" :key="msg.id" :class="msg.role === 'assistant' ? 'mr-8 bg-slate-100' : 'ml-8 bg-blue-100'" class="rounded-lg p-3 text-sm">
          <div class="mb-1 text-xs font-semibold uppercase text-slate-500">{{ msg.role }}</div>
          <p class="whitespace-pre-wrap">{{ msg.message }}</p>
        </div>
      </div>

      <form class="flex gap-2" @submit.prevent="sendMessage">
        <input v-model="newMessage" class="flex-1 rounded-lg border px-3 py-2 outline-none ring-blue-300 focus:ring" placeholder="Digite sua mensagem..." required />
        <button class="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700" :disabled="loading">
          {{ loading ? 'Enviando...' : 'Enviar' }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { chatApi } from '../services/api'

const messages = ref([])
const newMessage = ref('')
const loading = ref(false)

async function loadHistory() {
  const { data } = await chatApi.history()
  messages.value = data
}

async function sendMessage() {
  if (!newMessage.value.trim()) return
  loading.value = true
  try {
    const { data } = await chatApi.send(newMessage.value)
    messages.value = data.history
    newMessage.value = ''
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>
