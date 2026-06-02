<template>
  <div class="dash">
    <header class="dash__head">
      <h1 class="dash__title">Panou de control</h1>
      <p class="dash__hello" v-if="me?.email">Salut, {{ me.email }}.</p>
    </header>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <section class="dash__tiles">
      <article class="tile tile--accent">
        <span class="tile__value">{{ overview?.pendingCampaigns ?? '—' }}</span>
        <span class="tile__label">Campanii în așteptare</span>
      </article>
      <article class="tile">
        <span class="tile__value">{{ overview?.approvedUpcoming ?? '—' }}</span>
        <span class="tile__label">Aprobate, viitoare</span>
      </article>
      <article class="tile">
        <span class="tile__value">{{ overview?.citizensActive ?? '—' }}</span>
        <span class="tile__label">Cetățeni activi</span>
      </article>
      <article class="tile">
        <span class="tile__value">{{ overview?.registrationsToday ?? '—' }}</span>
        <span class="tile__label">Înscrieri azi</span>
      </article>
    </section>

    <section class="dash__next">
      <h2 class="dash__subtitle">Acțiuni rapide</h2>
      <p>
        <NuxtLink to="/admin/campanii?status=pending">Vezi campaniile în așteptare</NuxtLink>
        pentru moderare, sau caută în <NuxtLink to="/admin/cetateni">cetățeni</NuxtLink>
        și <NuxtLink to="/admin/organizatori">organizatori</NuxtLink>.
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { AdminOverview } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — Panou', robots: 'noindex, nofollow' })

const { me } = useAdminAuth()
const { data: overview, error } = await useFetch<AdminOverview>('/api/admin/stats/overview', {
  key: 'admin-overview',
})
</script>

<style scoped>
.dash { display: flex; flex-direction: column; gap: var(--space-lg); max-width: 900px; }

.dash__head { display: flex; flex-direction: column; gap: var(--space-xs); }
.dash__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-2xl, 1.75rem);
  color: var(--color-text);
  margin: 0;
}
.dash__hello { color: var(--color-slate-500, #64748b); margin: 0; }

.dash__tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-md);
}

.tile {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-lg);
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.tile--accent { border-color: var(--color-accent); }

.tile__value {
  font-family: var(--font-heading, var(--font-body));
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-primary);
  line-height: 1;
}
.tile--accent .tile__value { color: var(--color-accent); }

.tile__label { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); }

.dash__next {
  padding: var(--space-lg);
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.dash__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text);
  margin: 0 0 var(--space-sm);
}
</style>
