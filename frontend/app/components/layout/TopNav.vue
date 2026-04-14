<template>
  <header class="top-nav">
    <nav class="container top-nav__inner" aria-label="Navigare principală">
      <NuxtLink to="/" class="top-nav__logo">
        Sterilizări Gratuite
      </NuxtLink>

      <button
        class="top-nav__toggle"
        :aria-expanded="menuOpen"
        aria-controls="main-menu"
        @click="menuOpen = !menuOpen"
      >
        <span class="sr-only">Meniu</span>
        <span class="top-nav__hamburger" />
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
const menuOpen = ref(false)

const links = [
  { to: '/', label: 'Acasă' },
  { to: '/campanii', label: 'Campanii' },
  { to: '/organizatori', label: 'Organizatori' },
  { to: '/despre', label: 'Despre noi' },
]
</script>

<style scoped>
.top-nav {
  border-bottom: 1px solid var(--color-border);
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
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
  text-decoration: none;
}

.top-nav__links {
  display: flex;
  gap: var(--space-lg);
  list-style: none;
}

.top-nav__links a {
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.top-nav__links a:hover,
.top-nav__links a.router-link-active {
  color: var(--color-primary);
  text-decoration: none;
}

.top-nav__toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-sm);
}

.top-nav__hamburger {
  display: block;
  width: 24px;
  height: 2px;
  background: var(--color-text);
  position: relative;
}

.top-nav__hamburger::before,
.top-nav__hamburger::after {
  content: '';
  position: absolute;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--color-text);
}

.top-nav__hamburger::before { top: -7px; }
.top-nav__hamburger::after { top: 7px; }

@media (max-width: 768px) {
  .top-nav__toggle {
    display: block;
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
  }

  .top-nav__links--open {
    display: flex;
  }

  .top-nav__inner {
    position: relative;
  }
}
</style>
