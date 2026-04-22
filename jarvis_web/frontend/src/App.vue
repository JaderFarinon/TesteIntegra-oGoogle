<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <div class="flex min-h-screen">
      <AppSidebar :items="menuItems" :open="sidebarOpen" @close="sidebarOpen = false" />

      <div class="flex min-w-0 flex-1 flex-col lg:ml-72">
        <AppHeader :title="currentTitle" @toggle-sidebar="sidebarOpen = !sidebarOpen" />

        <main class="flex-1 p-4 sm:p-6">
          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'

const route = useRoute()
const sidebarOpen = ref(false)

const menuItems = [
  { path: '/', label: 'Início' },
  { path: '/assistente', label: 'Assistente' },
  { path: '/tarefas', label: 'Tarefas' },
  { path: '/compromissos', label: 'Compromissos' },
  { path: '/notas', label: 'Notas' },
  { path: '/gastos', label: 'Gastos' },
  { path: '/lembretes', label: 'Lembretes' },
  { path: '/configuracoes', label: 'Configurações' },
]

const currentTitle = computed(() => menuItems.find((item) => item.path === route.path)?.label || 'Jarvis')
</script>
