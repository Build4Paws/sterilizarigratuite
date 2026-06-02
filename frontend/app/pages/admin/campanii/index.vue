<template>
  <div class="page">
    <h1 class="page__title">Campanii</h1>

    <nav class="tabs">
      <NuxtLink
        v-for="t in tabs"
        :key="t.value"
        :to="t.value ? `/admin/campanii?status=${t.value}` : '/admin/campanii'"
        :class="['tabs__tab', { 'tabs__tab--active': activeStatus === t.value }]"
      >
        {{ t.label }}
      </NuxtLink>
    </nav>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <AdminTable
      :columns="['Organizație', 'Localitate', 'Județ', 'Perioadă', 'Status', '']"
      :empty="!pending && (data?.campaigns?.length ?? 0) === 0"
      empty-text="Nicio campanie pentru acest filtru."
    >
      <tr v-for="c in data?.campaigns ?? []" :key="c.submissionId" class="is-clickable" @click="open(c.submissionId)">
        <td>{{ c.organizationName }}</td>
        <td>{{ c.locality }}</td>
        <td>{{ c.countyName }}</td>
        <td>{{ formatDateRange(c.dateStart, c.dateEnd ?? undefined) }}</td>
        <td><AdminStatusBadge :status="c.status" /></td>
        <td><NuxtLink :to="`/admin/campanii/${c.submissionId}`" @click.stop>Detalii →</NuxtLink></td>
      </tr>
    </AdminTable>
  </div>
</template>

<script setup lang="ts">
import type { AdminCampaignList } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — Campanii', robots: 'noindex, nofollow' })

const route = useRoute()
const activeStatus = computed(() => String(route.query.status ?? ''))

const tabs = [
  { value: '', label: 'Toate' },
  { value: 'pending', label: 'În așteptare' },
  { value: 'approved', label: 'Aprobate' },
  { value: 'rejected', label: 'Respinse' },
  { value: 'cancelled', label: 'Anulate' },
  { value: 'finished', label: 'Finalizate' },
]

const { data, pending, error } = await useFetch<AdminCampaignList>('/api/admin/campaigns', {
  key: 'admin-campaigns',
  query: { status: activeStatus },
})

function open(id: string) {
  navigateTo(`/admin/campanii/${id}`)
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
.tabs { display: flex; flex-wrap: wrap; gap: var(--space-xs); }
.tabs__tab {
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-slate-500, #64748b);
  text-decoration: none;
  border: 1px solid transparent;
}
.tabs__tab:hover { background: var(--color-slate-50); }
.tabs__tab--active { background: var(--color-primary); color: var(--color-text-light); }
</style>
