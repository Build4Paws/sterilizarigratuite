<template>
  <div class="page">
    <h1 class="page__title">Jurnal audit</h1>
    <p class="page__note">Acțiuni de administrare și evenimente de sistem (GDPR Art. 30).</p>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <AdminTable
      :columns="['Când', 'Actor', 'Acțiune', 'Entitate', 'Detalii']"
      :empty="!pending && (data?.entries?.length ?? 0) === 0"
      empty-text="Nicio intrare."
    >
      <tr v-for="e in data?.entries ?? []" :key="e.id">
        <td class="nowrap">{{ formatDateTime(e.occurredAt) }}</td>
        <td>{{ e.actor || '—' }}</td>
        <td><code>{{ e.action }}</code></td>
        <td>{{ e.entityType }}{{ e.entityId != null ? ` #${e.entityId}` : '' }}</td>
        <td class="meta">{{ metaText(e.metadata) }}</td>
      </tr>
    </AdminTable>
  </div>
</template>

<script setup lang="ts">
import type { AuditList } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — Jurnal audit', robots: 'noindex, nofollow' })

const { data, pending, error } = await useFetch<AuditList>('/api/admin/audit', { key: 'admin-audit' })

function metaText(meta?: Record<string, unknown> | null): string {
  if (!meta || Object.keys(meta).length === 0) return '—'
  return Object.entries(meta).map(([k, v]) => `${k}: ${v}`).join(', ')
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 1000px; }
.page__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-2xl, 1.75rem);
  color: var(--color-text);
  margin: 0;
}
.page__note { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); margin: 0; }
.nowrap { white-space: nowrap; }
.meta { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); }
code { font-size: 0.8rem; }
</style>
