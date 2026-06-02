<template>
  <div class="admin">
    <aside class="admin__sidebar">
      <NuxtLink to="/admin" class="admin__brand">
        <PawPrint :size="22" />
        <span>Build4Paws <strong>Admin</strong></span>
      </NuxtLink>

      <nav class="admin__nav">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.disabled ? '' : item.to"
          :class="['admin__link', { 'admin__link--disabled': item.disabled }]"
          :aria-disabled="item.disabled"
          @click="item.disabled && $event.preventDefault()"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
          <span v-if="item.disabled" class="admin__soon">în curând</span>
        </NuxtLink>
      </nav>
    </aside>

    <div class="admin__main">
      <header class="admin__topbar">
        <div class="admin__user">
          <span v-if="me?.email" class="admin__email">{{ me.email }}</span>
          <UiButton variant="ghost" type="button" @click="logout">
            <LogOut :size="16" /> Ieși
          </UiButton>
        </div>
      </header>

      <main class="admin__content">
        <slot />
      </main>
    </div>

    <UiToaster />
  </div>
</template>

<script setup lang="ts">
import { PawPrint, LayoutDashboard, CalendarCheck, Users, Building2, ScrollText, LogOut } from 'lucide-vue-next'

const { me, logout } = useAdminAuth()

const nav = [
  { to: '/admin', label: 'Panou', icon: LayoutDashboard, disabled: false },
  { to: '/admin/campanii', label: 'Campanii', icon: CalendarCheck, disabled: false },
  { to: '/admin/cetateni', label: 'Cetățeni', icon: Users, disabled: false },
  { to: '/admin/organizatori', label: 'Organizatori', icon: Building2, disabled: false },
  { to: '/admin/audit', label: 'Jurnal audit', icon: ScrollText, disabled: false },
]
</script>

<style scoped>
.admin {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  background: var(--color-slate-50);
}

.admin__sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-lg) var(--space-md);
  background: var(--color-primary);
  color: var(--color-text-light);
}

.admin__brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-text-light);
  text-decoration: none;
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-lg);
}

.admin__brand strong { font-weight: 800; }

.admin__nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.admin__link {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-md);
  color: var(--color-text-light);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: 500;
  opacity: 0.85;
  transition: background-color 0.15s, opacity 0.15s;
}

.admin__link:hover { background: rgba(255, 255, 255, 0.1); opacity: 1; }
.admin__link.router-link-exact-active { background: rgba(255, 255, 255, 0.16); opacity: 1; }

.admin__link--disabled { opacity: 0.45; cursor: not-allowed; }
.admin__link--disabled:hover { background: transparent; opacity: 0.45; }

.admin__soon {
  margin-left: auto;
  font-size: 0.625rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.8;
}

.admin__main { display: flex; flex-direction: column; min-width: 0; }

.admin__topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-input-bg, #fff);
  border-bottom: 1px solid var(--color-border);
}

.admin__user { display: flex; align-items: center; gap: var(--space-md); }
.admin__email { font-size: var(--font-size-sm); color: var(--color-text); }

.admin__content { padding: var(--space-lg); flex: 1; }

@media (max-width: 720px) {
  .admin { grid-template-columns: 1fr; }
  .admin__sidebar { flex-direction: row; align-items: center; justify-content: space-between; }
  .admin__nav { flex-direction: row; flex-wrap: wrap; }
  .admin__soon { display: none; }
}
</style>
