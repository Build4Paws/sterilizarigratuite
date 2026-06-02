<template>
  <div class="admin">
    <aside class="admin__sidebar">
      <NuxtLink to="/admin" class="admin__brand">
        <img src="/favicon.svg" alt="" class="admin__logo" width="26" height="26" />
        <span>Build4Paws <strong>Admin</strong></span>
      </NuxtLink>

      <nav class="admin__nav">
        <template v-for="group in nav" :key="group.label">
          <p class="admin__group">{{ group.label }}</p>
          <NuxtLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="admin__link"
          >
            <component :is="item.icon" :size="18" class="admin__link-icon" />
            <span>{{ item.label }}</span>
            <span v-if="item.badge" class="admin__badge">{{ item.badge }}</span>
          </NuxtLink>
        </template>
      </nav>

      <div class="admin__sidebar-foot">
        <a href="/" target="_blank" rel="noopener" class="admin__site-link">
          <ExternalLink :size="14" /> Vezi site-ul public
        </a>
      </div>
    </aside>

    <div class="admin__main">
      <header class="admin__topbar">
        <h1 class="admin__page-title">{{ pageTitle }}</h1>
        <div class="admin__user">
          <div class="admin__avatar" :title="me?.email">{{ initial }}</div>
          <span v-if="me?.email" class="admin__email">{{ me.email }}</span>
          <UiButton variant="ghost" type="button" @click="logout">
            <LogOut :size="16" /> Ieși
          </UiButton>
        </div>
      </header>

      <main class="admin__content">
        <div :key="route.path" class="admin__page">
          <slot />
        </div>
      </main>
    </div>

    <UiToaster />
  </div>
</template>

<script setup lang="ts">
import { LayoutDashboard, CalendarCheck, Users, Building2, FileBarChart, ScrollText, LogOut, ExternalLink } from 'lucide-vue-next'
import type { AdminOverview } from '~/types'

const { me, logout } = useAdminAuth()
const route = useRoute()

// Shared (same key) with the dashboard fetch — powers the live "pending" badge.
const { data: overview } = useFetch<AdminOverview>('/api/admin/stats/overview', {
  key: 'admin-overview',
  default: () => null as unknown as AdminOverview,
})
const pending = computed(() => overview.value?.pendingCampaigns ?? 0)

const nav = computed(() => [
  {
    label: 'Principal',
    items: [
      { to: '/admin', label: 'Panou', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Gestionare',
    items: [
      { to: '/admin/campanii', label: 'Campanii', icon: CalendarCheck, badge: pending.value || undefined },
      { to: '/admin/cetateni', label: 'Cetățeni', icon: Users },
      { to: '/admin/organizatori', label: 'Organizatori', icon: Building2 },
    ],
  },
  {
    label: 'Analiză',
    items: [
      { to: '/admin/rapoarte', label: 'Rapoarte', icon: FileBarChart },
      { to: '/admin/audit', label: 'Jurnal audit', icon: ScrollText },
    ],
  },
])

const initial = computed(() => (me.value?.email?.[0] ?? '?').toUpperCase())

const pageTitle = computed(() => {
  const p = route.path
  if (p === '/admin') return 'Panou de control'
  if (p.startsWith('/admin/campanii')) return 'Campanii'
  if (p.startsWith('/admin/cetateni')) return 'Cetățeni'
  if (p.startsWith('/admin/organizatori')) return 'Organizatori'
  if (p.startsWith('/admin/rapoarte')) return 'Rapoarte'
  if (p.startsWith('/admin/audit')) return 'Jurnal audit'
  return 'Admin'
})
</script>

<style scoped>
.admin {
  display: grid;
  grid-template-columns: 248px 1fr;
  min-height: 100vh;
  background: var(--color-slate-50);
}

/* --- Sidebar --- */
.admin__sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  padding: var(--space-lg) var(--space-md);
  background: var(--color-primary);
  color: var(--color-text-light);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.admin__brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-text-light);
  text-decoration: none;
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-lg);
  padding: 0 var(--space-xs);
}
.admin__brand strong { font-weight: 800; }
/* Brand mark is navy (#18073d) — render it white on the dark sidebar. */
.admin__logo { width: 26px; height: 26px; filter: brightness(0) invert(1); }

.admin__nav { display: flex; flex-direction: column; gap: var(--space-xs); }

.admin__group {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.45);
  padding: var(--space-sm) var(--space-sm) var(--space-xs);
  margin: 0;
}
.admin__group:not(:first-child) { margin-top: var(--space-sm); }

.admin__link {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-md);
  color: var(--color-text-light);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: 600;
  opacity: 0.8;
  transition: background-color 0.18s ease, opacity 0.18s ease, transform 0.18s ease;
}
.admin__link-icon { flex-shrink: 0; transition: color 0.18s ease; }
.admin__link:hover { background: rgba(255, 255, 255, 0.08); opacity: 1; transform: translateX(2px); }

.admin__link.router-link-exact-active,
.admin__link.router-link-active {
  background: rgba(255, 255, 255, 0.12);
  opacity: 1;
}
/* Accent bar on the active item. */
.admin__link.router-link-active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-md));
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  background: var(--color-accent);
}
.admin__link.router-link-active .admin__link-icon { color: var(--color-accent); }

/* Don't let the parent "/admin" stay active on child routes. */
.admin__link[href="/admin"].router-link-active:not(.router-link-exact-active) {
  background: transparent;
  opacity: 0.8;
}
.admin__link[href="/admin"].router-link-active:not(.router-link-exact-active)::before { display: none; }
.admin__link[href="/admin"].router-link-active:not(.router-link-exact-active) .admin__link-icon { color: currentColor; }

.admin__badge {
  margin-left: auto;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.375rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent);
  color: var(--color-text-light);
  border-radius: var(--radius-full);
  font-size: 0.6875rem;
  font-weight: 800;
  line-height: 1;
}

.admin__sidebar-foot { margin-top: auto; padding: 0 var(--space-xs); }
.admin__site-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: rgba(255, 255, 255, 0.6);
  font-size: var(--font-size-sm);
  text-decoration: none;
  transition: color 0.18s ease;
}
.admin__site-link:hover { color: var(--color-text-light); text-decoration: none; }

/* --- Main --- */
.admin__main { display: flex; flex-direction: column; min-width: 0; }

.admin__topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-xl);
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border-light);
  position: sticky;
  top: 0;
  z-index: 10;
}
.admin__page-title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-lg);
  color: var(--color-text);
  margin: 0;
}

.admin__user { display: flex; align-items: center; gap: var(--space-sm); }
.admin__avatar {
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-text-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: var(--font-size-sm);
  flex-shrink: 0;
}
.admin__email { font-size: var(--font-size-sm); color: var(--color-text-muted); }

.admin__content { padding: var(--space-xl); flex: 1; }

/* Subtle entrance on each route change (keyed wrapper). */
.admin__page { animation: adminPageIn 0.26s ease both; }
@keyframes adminPageIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  .admin__page { animation: none; }
  .admin__link:hover { transform: none; }
}

/* --- Responsive --- */
@media (max-width: 860px) {
  .admin { grid-template-columns: 1fr; }
  .admin__sidebar {
    position: static;
    height: auto;
    flex-direction: column;
    gap: var(--space-md);
  }
  .admin__nav { gap: var(--space-xs); }
  .admin__sidebar-foot { margin-top: 0; }
  .admin__email { display: none; }
  .admin__topbar { padding: var(--space-md); }
  .admin__content { padding: var(--space-md); }
  .admin__link.router-link-active::before { display: none; }
}
</style>
