<template>
  <div class="page">
    <NuxtLink to="/admin/organizatori" class="back">← Înapoi la organizatori</NuxtLink>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <div v-if="o" class="detail">
      <h1 class="detail__title">{{ o.name }}</h1>

      <section class="card">
        <dl class="kv">
          <div><dt>Email</dt><dd>{{ o.contactEmail }}</dd></div>
          <div><dt>Telefon</dt><dd>{{ formatPhone(o.contactPhone) }}</dd></div>
          <div><dt>Înregistrat</dt><dd>{{ formatDateTime(o.createdAt) }}</dd></div>
        </dl>
        <p v-if="o.notes" class="notes">{{ o.notes }}</p>
      </section>

      <section>
        <h2 class="card__title">Campaniile organizatorului</h2>
        <AdminTable
          :columns="['Localitate', 'Perioadă', 'Status', '']"
          :empty="(o.campaigns?.length ?? 0) === 0"
          empty-text="Nicio campanie."
        >
          <tr v-for="c in o.campaigns" :key="c.submissionId">
            <td>{{ c.locality }}, {{ c.countyName }}</td>
            <td>{{ formatDateRange(c.dateStart, c.dateEnd ?? undefined) }}</td>
            <td><AdminStatusBadge :status="c.status" /></td>
            <td><NuxtLink :to="`/admin/campanii/${c.submissionId}`">Detalii →</NuxtLink></td>
          </tr>
        </AdminTable>
      </section>
    </div>

    <p v-else-if="!pending" class="empty">Organizatorul nu a fost găsit.</p>
  </div>
</template>

<script setup lang="ts">
import type { AdminOrganizerDetail } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — Detalii organizator', robots: 'noindex, nofollow' })

const route = useRoute()
const id = computed(() => String(route.params.id))

const { data: o, pending, error } = await useFetch<AdminOrganizerDetail>(
  () => `/api/admin/organizers/${id.value}`,
  { key: `admin-organizer-${id.value}` },
)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 900px; }
.back { font-size: var(--font-size-sm); color: var(--color-primary); text-decoration: none; }
.back:hover { text-decoration: underline; }
.detail { display: flex; flex-direction: column; gap: var(--space-md); }
.detail__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-xl);
  color: var(--color-text);
  margin: 0;
}
.card {
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}
.card__title { font-size: var(--font-size-base); color: var(--color-text); margin: 0 0 var(--space-sm); }
.kv { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-sm) var(--space-lg); margin: 0; }
.kv dt { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); }
.kv dd { margin: 0.125rem 0 0; color: var(--color-text); }
.notes { margin-top: var(--space-md); font-size: var(--font-size-sm); color: var(--color-text); }
.empty { color: var(--color-slate-500, #64748b); }
</style>
