<template>
  <div class="max-w-2xl space-y-4">
    <PageCard>
      <h3 class="text-lg font-semibold">Configurações da OpenAI</h3>
      <p class="mt-1 text-sm text-slate-500">Salve a chave e o modelo utilizados pelo backend FastAPI.</p>

      <form class="mt-4 space-y-3" @submit.prevent="saveSettings">
        <label class="block space-y-1 text-sm">
          <span class="font-medium text-slate-700">Chave da OpenAI</span>
          <input
            v-model="form.openai_api_key"
            type="password"
            placeholder="sk-..."
            class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring"
          />
        </label>

        <label class="block space-y-1 text-sm">
          <span class="font-medium text-slate-700">Modelo da OpenAI</span>
          <input
            v-model="form.openai_model"
            type="text"
            placeholder="gpt-4.1-mini"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none ring-slate-300 focus:ring"
          />
        </label>

        <button class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" :disabled="loading">
          {{ loading ? 'Salvando...' : 'Salvar' }}
        </button>
      </form>
    </PageCard>

    <FeedbackAlert :type="feedbackType" :message="feedbackMessage" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import PageCard from '../components/shared/PageCard.vue'
import FeedbackAlert from '../components/shared/FeedbackAlert.vue'
import { settingsApi } from '../services/api'

const loading = ref(false)
const feedbackType = ref('info')
const feedbackMessage = ref('')
const form = reactive({
  openai_api_key: '',
  openai_model: 'gpt-4.1-mini',
})

async function loadSettings() {
  loading.value = true
  feedbackMessage.value = ''
  try {
    const { data } = await settingsApi.fetch()
    if (!data) {
      feedbackType.value = 'info'
      feedbackMessage.value = 'Nenhuma configuração salva ainda. Preencha os campos e clique em Salvar.'
      return
    }
    form.openai_api_key = data.openai_api_key || ''
    form.openai_model = data.openai_model || 'gpt-4.1-mini'
    feedbackType.value = 'success'
    feedbackMessage.value = 'Configuração carregada com sucesso.'
  } catch (error) {
    feedbackType.value = 'error'
    feedbackMessage.value = error?.response?.data?.detail || 'Falha ao carregar configurações.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  loading.value = true
  feedbackMessage.value = ''
  try {
    await settingsApi.save({ ...form })
    feedbackType.value = 'success'
    feedbackMessage.value = 'Configurações salvas com sucesso.'
  } catch (error) {
    feedbackType.value = 'error'
    feedbackMessage.value = error?.response?.data?.detail || 'Falha ao salvar configurações.'
  } finally {
    loading.value = false
  }
}

onMounted(loadSettings)
</script>
