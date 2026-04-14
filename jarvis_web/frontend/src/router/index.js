import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import ModuleView from '../views/ModuleView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', name: 'chat', component: ChatView },
  {
    path: '/tarefas',
    name: 'tasks',
    component: ModuleView,
    props: { moduleKey: 'tasks', title: 'Tarefas' },
  },
  {
    path: '/compromissos',
    name: 'appointments',
    component: ModuleView,
    props: { moduleKey: 'appointments', title: 'Compromissos' },
  },
  {
    path: '/notas',
    name: 'notes',
    component: ModuleView,
    props: { moduleKey: 'notes', title: 'Notas' },
  },
  {
    path: '/gastos',
    name: 'expenses',
    component: ModuleView,
    props: { moduleKey: 'expenses', title: 'Gastos' },
  },
  {
    path: '/lembretes',
    name: 'reminders',
    component: ModuleView,
    props: { moduleKey: 'reminders', title: 'Lembretes' },
  },
  { path: '/configuracoes', name: 'settings', component: SettingsView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
