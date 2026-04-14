<template>
  <section class="mx-auto max-w-3xl space-y-4">
    <header>
      <h1 class="text-2xl font-semibold">Configurações</h1>
      <p class="text-sm text-slate-600">Informações atuais do backend e ambiente.</p>
    </header>

    <div class="rounded-xl border bg-white p-4">
      <dl class="space-y-2 text-sm">
        <div class="flex justify-between border-b pb-2">
          <dt class="font-medium">Aplicação</dt>
          <dd>{{ info.app_name }}</dd>
        </div>
        <div class="flex justify-between border-b pb-2">
          <dt class="font-medium">Ambiente</dt>
          <dd>{{ info.app_env }}</dd>
        </div>
        <div class="flex justify-between pb-2">
          <dt class="font-medium">Modelo OpenAI</dt>
          <dd>{{ info.openai_model }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { settingsApi } from '../services/api'

const info = ref({
  app_name: '',
  app_env: '',
  openai_model: '',
})

onMounted(async () => {
  const { data } = await settingsApi.fetch()
  info.value = data
})
</script>
