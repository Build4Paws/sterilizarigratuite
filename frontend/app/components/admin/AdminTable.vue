<template>
  <div class="atable-wrap">
    <table class="atable">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">{{ col }}</th>
        </tr>
      </thead>
      <tbody>
        <slot />
      </tbody>
    </table>
    <p v-if="empty" class="atable__empty">{{ emptyText ?? 'Niciun rezultat.' }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ columns: string[]; empty?: boolean; emptyText?: string }>()
</script>

<style scoped>
.atable-wrap {
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.atable {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.atable thead th {
  text-align: left;
  padding: 0.625rem 0.875rem;
  background: var(--color-slate-50);
  color: var(--color-slate-500, #64748b);
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
/* Rows are slotted from the parent, so reach them with :deep. */
.atable :deep(td) {
  padding: 0.75rem 0.875rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  vertical-align: middle;
}
.atable :deep(tbody tr:last-child td) { border-bottom: none; }
.atable :deep(tbody tr) { transition: background-color 0.12s; }
.atable :deep(tbody tr.is-clickable) { cursor: pointer; }
.atable :deep(tbody tr.is-clickable:hover) { background: var(--color-slate-50); }
.atable :deep(a) { color: var(--color-primary); font-weight: 600; text-decoration: none; }
.atable :deep(a:hover) { text-decoration: underline; }
.atable__empty {
  padding: var(--space-lg);
  text-align: center;
  color: var(--color-slate-500, #64748b);
  font-size: var(--font-size-sm);
}
</style>
