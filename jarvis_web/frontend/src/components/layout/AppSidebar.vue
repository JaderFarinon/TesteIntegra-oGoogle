<template>
  <div>
    <div v-if="open" class="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" @click="$emit('close')"></div>

    <aside
      :class="[
        'fixed left-0 top-0 z-40 h-full w-72 border-r border-slate-200 bg-white p-4 transition-transform duration-200',
        open ? 'translate-x-0' : '-translate-x-full',
        'lg:translate-x-0',
      ]"
    >
      <div class="mb-6 border-b border-slate-200 pb-4">
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-500">Jarvis</p>
        <h1 class="text-2xl font-bold text-slate-900">Jarvis</h1>
      </div>

      <nav class="space-y-1">
        <RouterLink
          v-for="item in items"
          :key="item.path"
          :to="item.path"
          class="block rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
          active-class="bg-slate-900 text-white hover:bg-slate-900 hover:text-white"
          @click="$emit('close')"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, required: true },
  open: { type: Boolean, default: false },
})

defineEmits(['close'])
</script>
