<template>
  <div class="min-h-screen bg-slate-100 text-slate-900 md:flex">
    <aside class="w-full border-b bg-slate-900 text-white md:min-h-screen md:w-64 md:border-b-0 md:border-r">
      <div class="border-b border-slate-700 p-4 text-lg font-bold">Jarvis Web</div>
      <nav class="grid grid-cols-2 gap-2 p-3 md:grid-cols-1">
        <RouterLink v-for="item in menu" :key="item.path" :to="item.path" class="rounded-lg px-3 py-2 text-sm hover:bg-slate-700" active-class="bg-slate-700">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <main class="flex-1 p-4 md:p-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
const menu = [
  { path: '/chat', label: 'Assistente' },
  { path: '/tarefas', label: 'Tarefas' },
  { path: '/compromissos', label: 'Compromissos' },
  { path: '/notas', label: 'Notas' },
  { path: '/gastos', label: 'Gastos' },
  { path: '/lembretes', label: 'Lembretes' },
  { path: '/configuracoes', label: 'Configurações' },
]
</script>
