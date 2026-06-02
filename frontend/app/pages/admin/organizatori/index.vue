<template>
  <div class="page">
    <AdminFilters
      v-model:search="filters.search.value"
      search-placeholder="Caută după nume, email sau telefon…"
      :has-active="filters.hasActive.value"
      @reset="filters.reset"
    />

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <AdminTable
      :columns="['Nume', 'Email', 'Telefon', 'Campanii', 'Creat', '']"
      :empty="!pending && (data?.organizers?.length ?? 0) === 0"
      :empty-text="emptyText"
    >
      <tr v-for="o in data?.organizers ?? []" :key="o.organizerId" class="is-clickable" @click="open(o.organizerId)">
        <td>{{ o.name }}</td>
        <td>{{ o.contactEmail }}</td>
        <td>{{ formatPhone(o.contactPhone) }}</td>
        <td>{{ o.campaignCount }}</td>
        <td>{{ formatDate(o.createdAt.slice(0, 10)) }}</td>
        <td><NuxtLink :to="`/admin/organizatori/${o.organizerId}`" @click.stop>Detalii →</NuxtLink></td>
      </tr>
    </AdminTable>
  </div>
</template>

<script setup lang="ts">
import type { AdminOrganizerList } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — Organizatori', robots: 'noindex, nofollow' })

const route = useRoute()
const filters = useAdminListFilters()

const { data, pending, error } = await useFetch<AdminOrganizerList>('/api/admin/organizers', {
  key: 'admin-organizers',
  query: {
    q: computed(() => route.query.q || undefined),
  },
})

const emptyText = computed(() =>
  filters.hasActive.value ? 'Niciun organizator pentru această căutare.' : 'Niciun organizator încă.')

function open(id: string) {
  navigateTo(`/admin/organizatori/${id}`)
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 1000px; }
</style>
