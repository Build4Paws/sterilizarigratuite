<template>
  <div class="dash">
    <p v-if="me?.email" class="dash__hello">Salut, <strong>{{ me.email }}</strong> 👋</p>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <section class="dash__tiles">
      <NuxtLink to="/admin/campanii?status=pending" class="tile tile--accent tile--link">
        <span class="tile__icon"><Clock :size="20" /></span>
        <span class="tile__value">{{ overview?.pendingCampaigns ?? '–' }}</span>
        <span class="tile__label">Campanii în așteptare</span>
        <span class="tile__cta">Moderează →</span>
      </NuxtLink>

      <article class="tile">
        <span class="tile__icon"><CalendarCheck :size="20" /></span>
        <span class="tile__value">{{ overview?.approvedUpcoming ?? '–' }}</span>
        <span class="tile__label">Aprobate, viitoare</span>
      </article>

      <NuxtLink to="/admin/cetateni" class="tile tile--link">
        <span class="tile__icon"><Users :size="20" /></span>
        <span class="tile__value">{{ overview?.citizensActive ?? '–' }}</span>
        <span class="tile__label">Cetățeni activi</span>
        <span class="tile__cta">Vezi lista →</span>
      </NuxtLink>

      <article class="tile">
        <span class="tile__icon"><UserPlus :size="20" /></span>
        <span class="tile__value">{{ overview?.registrationsToday ?? '–' }}</span>
        <span class="tile__label">Înscrieri azi</span>
      </article>
    </section>

    <section class="dash__actions">
      <h2 class="dash__subtitle">Acțiuni rapide</h2>
      <div class="dash__action-grid">
        <NuxtLink
          v-for="a in quickActions"
          :key="a.to"
          :to="a.to"
          class="action"
        >
          <span class="action__icon"><component :is="a.icon" :size="18" /></span>
          <span class="action__body">
            <span class="action__title">{{ a.title }}</span>
            <span class="action__desc">{{ a.desc }}</span>
          </span>
          <ChevronRight :size="18" class="action__arrow" />
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Clock, CalendarCheck, Users, UserPlus, Building2, FileBarChart, ChevronRight } from 'lucide-vue-next'
import type { AdminOverview } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin · Panou', robots: 'noindex, nofollow' })

const { me } = useAdminAuth()
const { data: overview, error } = await useFetch<AdminOverview>('/api/admin/stats/overview', {
  key: 'admin-overview',
})

const quickActions = [
  { to: '/admin/campanii?status=pending', icon: Clock, title: 'Moderează campanii', desc: 'Aprobă sau respinge submisiile în așteptare.' },
  { to: '/admin/cetateni', icon: Users, title: 'Caută cetățeni', desc: 'Listă minimizată, detalii PII auditabile.' },
  { to: '/admin/organizatori', icon: Building2, title: 'Organizatori', desc: 'ONG-uri și primării înscrise.' },
  { to: '/admin/rapoarte', icon: FileBarChart, title: 'Generează rapoarte', desc: 'Exporturi CSV pe filtre.' },
]
</script>

<style scoped>
.dash { display: flex; flex-direction: column; gap: var(--space-xl); max-width: 940px; }
.dash__hello { color: var(--color-text-muted); margin: 0; font-size: var(--font-size-base); }
.dash__hello strong { color: var(--color-text); }

.dash__tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: var(--space-md);
}

.tile {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-decoration: none;
  overflow: hidden;
}
.tile__icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: var(--radius-md);
  background: var(--color-slate-100);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-xs);
}
.tile--accent { border-color: var(--color-accent); }
.tile--accent .tile__icon { background: var(--color-accent); color: var(--color-text-light); }

.tile__value {
  font-family: var(--font-heading, var(--font-body));
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--color-primary);
  line-height: 1;
}
.tile--accent .tile__value { color: var(--color-accent); }
.tile__label { font-size: var(--font-size-sm); color: var(--color-text-muted); }

.tile--link { cursor: pointer; transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease; }
.tile--link:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(4, 26, 73, 0.1); }
.tile__cta {
  font-size: var(--font-size-sm);
  font-weight: 700;
  color: var(--color-accent);
  margin-top: var(--space-xs);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.16s ease, transform 0.16s ease;
}
.tile--link:hover .tile__cta { opacity: 1; transform: translateX(0); }

/* --- Quick actions --- */
.dash__subtitle {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-lg);
  color: var(--color-text);
  margin: 0 0 var(--space-md);
}
.dash__action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-md);
}
.action {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: border-color 0.16s ease, transform 0.16s ease;
}
.action:hover { border-color: var(--color-primary); transform: translateX(2px); text-decoration: none; }
.action__icon {
  flex-shrink: 0;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: var(--radius-md);
  background: var(--color-slate-100);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.action__body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.action__title { font-weight: 700; color: var(--color-text); }
.action__desc { font-size: var(--font-size-sm); color: var(--color-text-muted); }
.action__arrow { margin-left: auto; color: var(--color-text-muted); flex-shrink: 0; }

@media (prefers-reduced-motion: reduce) {
  .tile--link:hover, .action:hover { transform: none; }
}
</style>
