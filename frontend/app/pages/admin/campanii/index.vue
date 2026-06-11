<template>
  <div class="page">
    <nav class="tabs">
      <NuxtLink
        v-for="t in tabs"
        :key="t.value"
        :to="{ path: '/admin/campanii', query: tabQuery(t.value) }"
        :class="['tabs__tab', { 'tabs__tab--active': activeStatus === t.value }]"
      >
        {{ t.label }}
      </NuxtLink>
    </nav>

    <AdminFilters
      v-model:search="filters.search.value"
      v-model:county="filters.county.value"
      :counties="filters.counties.value"
      show-county
      search-placeholder="Caută după organizație sau localitate…"
      :has-active="filters.hasActive.value"
      @reset="filters.reset"
    />

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <AdminTable
      :columns="['Organizație', 'Localitate', 'Județ', 'Perioadă', 'Status', '']"
      :empty="!pending && (data?.campaigns?.length ?? 0) === 0"
      :empty-text="emptyText"
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
useSeoMeta({ title: 'Admin · Campanii', robots: 'noindex, nofollow' })

const route = useRoute()
const activeStatus = computed(() => String(route.query.status ?? ''))

const filters = useAdminListFilters({ county: true })
await filters.init()

const tabs = [
  { value: '', label: 'Toate' },
  { value: 'pending', label: 'În așteptare' },
  { value: 'approved', label: 'Aprobate' },
  { value: 'rejected', label: 'Respinse' },
  { value: 'cancelled', label: 'Anulate' },
  { value: 'finished', label: 'Finalizate' },
]

/** Switch status while keeping the active search/county filters. */
function tabQuery(status: string) {
  const q: Record<string, string | undefined> = { ...route.query } as Record<string, string | undefined>
  q.status = status || undefined
  return q
}

const { data, pending, error } = await useFetch<AdminCampaignList>('/api/admin/campaigns', {
  key: 'admin-campaigns',
  query: {
    status: computed(() => route.query.status || undefined),
    county: computed(() => route.query.county || undefined),
    q: computed(() => route.query.q || undefined),
  },
})

const emptyText = computed(() =>
  filters.hasActive.value || activeStatus.value
    ? 'Nicio campanie pentru aceste filtre.'
    : 'Nicio campanie încă.')

function open(id: string) {
  navigateTo(`/admin/campanii/${id}`)
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 1000px; }
.tabs { display: flex; flex-wrap: wrap; gap: var(--space-xs); }
.tabs__tab {
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  text-decoration: none;
}
.tabs__tab:hover { background: var(--color-slate-50); }
.tabs__tab--active { background: var(--color-primary); color: var(--color-text-light); }
</style>
