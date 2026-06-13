<template>
  <div class="page">
    <p class="page__note">
      Lista afișează date minime. Telefonul și emailul sunt vizibile doar în
      pagina de detalii, iar accesul este înregistrat în jurnalul de audit.
    </p>

    <nav class="tabs">
      <NuxtLink
        v-for="t in tabs"
        :key="t.value"
        :to="{ path: '/admin/cetateni', query: tabQuery(t.value) }"
        :class="['tabs__tab', { 'tabs__tab--active': activeStatus === t.value }]"
      >
        {{ t.label }}
      </NuxtLink>
    </nav>

    <AdminFilters
      v-model:search="filters.search.value"
      v-model:county="filters.county.value"
      v-model:locality="filters.locality.value"
      :counties="filters.counties.value"
      :localities="filters.localities.value"
      show-county
      show-locality
      search-placeholder="Caută după nume…"
      :has-active="filters.hasActive.value"
      @reset="filters.reset"
    />

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <AdminTable
      :columns="['Nume', 'Localitate', 'Județ', 'Canale', 'Status', 'Înscris', '']"
      :empty="!pending && (data?.citizens?.length ?? 0) === 0"
      :empty-text="emptyText"
    >
      <tr v-for="z in data?.citizens ?? []" :key="z.citizenId" class="is-clickable" @click="open(z.citizenId)">
        <td>{{ z.name }}</td>
        <td>{{ z.locality }}</td>
        <td>{{ z.countyName }}</td>
        <td>
          <span v-if="z.channelMask.phone" class="chip">Tel</span>
          <span v-if="z.channelMask.email" class="chip">Email</span>
        </td>
        <td><AdminStatusBadge :status="z.status" /></td>
        <td>{{ formatDate(z.createdAt.slice(0, 10)) }}</td>
        <td><NuxtLink :to="`/admin/cetateni/${z.citizenId}`" @click.stop>Detalii →</NuxtLink></td>
      </tr>
    </AdminTable>
  </div>
</template>

<script setup lang="ts">
import type { AdminCitizenList } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin · Cetățeni', robots: 'noindex, nofollow' })

const route = useRoute()
const activeStatus = computed(() => String(route.query.status ?? ''))

const filters = useAdminListFilters({ county: true, locality: true })
await filters.init()

const tabs = [
  { value: '', label: 'Toți' },
  { value: 'active', label: 'Activi' },
  { value: 'pending_confirm', label: 'Neconfirmați' },
  { value: 'unsubscribed', label: 'Dezabonați' },
  { value: 'deleted', label: 'Șterși' },
]

/** Switch status while keeping the active search/county/locality filters. */
function tabQuery(status: string) {
  const q: Record<string, string | undefined> = { ...route.query } as Record<string, string | undefined>
  q.status = status || undefined
  return q
}

const { data, pending, error } = await useFetch<AdminCitizenList>('/api/admin/citizens', {
  key: 'admin-citizens',
  query: {
    status: computed(() => route.query.status || undefined),
    county: computed(() => route.query.county || undefined),
    locality: computed(() => route.query.locality || undefined),
    q: computed(() => route.query.q || undefined),
  },
})

const emptyText = computed(() =>
  filters.hasActive.value || activeStatus.value
    ? 'Niciun cetățean pentru aceste filtre.'
    : 'Niciun cetățean încă.')

function open(id: string) {
  navigateTo(`/admin/cetateni/${id}`)
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 1000px; }
.page__note { font-size: var(--font-size-sm); color: var(--color-text-muted); margin: 0; }
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
.chip {
  display: inline-block;
  margin-right: 0.25rem;
  padding: 0.0625rem 0.4rem;
  border-radius: var(--radius-md);
  background: var(--color-slate-50);
  font-size: 0.7rem;
  color: var(--color-text-muted);
}
</style>
