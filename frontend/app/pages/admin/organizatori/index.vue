<template>
  <div class="page">
    <h1 class="page__title">Organizatori</h1>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <AdminTable
      :columns="['Nume', 'Email', 'Telefon', 'Campanii', 'Creat', '']"
      :empty="!pending && (data?.organizers?.length ?? 0) === 0"
      empty-text="Niciun organizator."
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

const { data, pending, error } = await useFetch<AdminOrganizerList>('/api/admin/organizers', { key: 'admin-organizers' })

function open(id: string) {
  navigateTo(`/admin/organizatori/${id}`)
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
</style>
