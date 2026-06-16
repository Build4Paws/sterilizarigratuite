<template>
  <header class="top-nav">
    <nav class="container top-nav__inner" aria-label="Navigare principală">
      <NuxtLink to="/" class="top-nav__logo">
        <img src="~/assets/images/logo-horizontal.svg" alt="Build4Paws" class="top-nav__logo-img" />
      </NuxtLink>

      <button
        class="top-nav__toggle"
        :aria-expanded="menuOpen"
        aria-controls="main-menu"
        @click="menuOpen = !menuOpen"
      >
        <span class="sr-only">Meniu</span>
        <Menu v-if="!menuOpen" :size="24" />
        <X v-else :size="24" />
      </button>

      <ul id="main-menu" class="top-nav__links" :class="{ 'top-nav__links--open': menuOpen }">
        <li v-for="link in links" :key="link.to">
          <NuxtLink :to="link.to" @click="menuOpen = false">
            {{ link.label }}
          </NuxtLink>
        </li>
      </ul>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { Menu, X } from 'lucide-vue-next'

const menuOpen = ref(false)

const links = [
  { to: '/', label: 'Acasă' },
  { to: '/campanii', label: 'Campanii' },
  { to: '/ghid-sterilizare', label: 'Ghid sterilizare' },
  { to: '/organizatori', label: 'Organizatori' },
  { to: '/harta', label: 'Harta' },
  { to: '/sustine', label: 'Doneaza' },
]
</script>

<style scoped>
.top-nav {
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg);
}

.top-nav__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--space-md);
  padding-bottom: var(--space-md);
}

.top-nav__logo {
  display: flex;
  align-items: center;
  text-decoration: none;
  letter-spacing: -0.01em;
}

.top-nav__logo:hover {
  text-decoration: none;
}

.top-nav__logo-icon {
  color: var(--color-accent);
}

.top-nav__logo strong {
  color: var(--color-accent);
}

.top-nav__logo:hover {
  text-decoration: none;
}

.top-nav__logo-img {
  height: 36px;
  width: auto;
}

.top-nav__links {
  display: flex;
  gap: var(--space-xl);
  list-style: none;
}

.top-nav__links a {
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-weight: 500;
  text-decoration: none;
  padding: var(--space-xs) 0;
  border-bottom: 2px solid transparent;
  transition: color 0.2s, border-color 0.2s;
}

.top-nav__links a:hover {
  color: var(--color-accent);
  text-decoration: none;
}

.top-nav__links a.router-link-exact-active {
  color: var(--color-primary);
  border-bottom-color: var(--color-accent);
}

.top-nav__toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-xs);
  color: var(--color-text);
}

@media (max-width: 768px) {
  .top-nav__toggle {
    display: flex;
    align-items: center;
  }

  .top-nav__links {
    display: none;
    flex-direction: column;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border);
    padding: var(--space-md);
    gap: var(--space-md);
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .top-nav__links--open {
    display: flex;
  }

  .top-nav__inner {
    position: relative;
  }
}
</style>
