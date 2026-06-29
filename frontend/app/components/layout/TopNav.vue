<template>
  <header class="top-nav" :class="{ 'top-nav--scrolled': scrolled }">
    <nav class="container top-nav__inner" aria-label="Navigare principală">
      <ul class="top-nav__links">
        <li v-for="link in links" :key="link.to">
          <NuxtLink :to="link.to" :aria-label="link.label" :title="link.label">
            <component :is="link.icon" :size="22" class="top-nav__icon" aria-hidden="true" />
            <span class="top-nav__label">{{ link.label }}</span>
          </NuxtLink>
        </li>
      </ul>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { Home, Megaphone, BookOpen, Users, MapPin, Heart } from 'lucide-vue-next'
import { useWindowScroll } from '@vueuse/core'

const links = [
  { to: '/', label: 'Acasă', icon: Home },
  { to: '/campanii', label: 'Campanii', icon: Users },
  { to: '/ghid-sterilizare', label: 'Ghid sterilizare', icon: BookOpen },
  { to: '/organizatori', label: 'Organizează', icon: Megaphone },
  { to: '/harta', label: 'Vezi harta', icon: MapPin },
  { to: '/sustine', label: 'Doneaza', icon: Heart },
]

// Scroll state drives the condensed / elevated "frosted" header treatment.
const { y } = useWindowScroll()

const SCROLL_ENTER = 64
const SCROLL_EXIT = 8
const scrolled = ref(false)
watch(y, (val) => {
  if (!scrolled.value && val > SCROLL_ENTER) scrolled.value = true
  else if (scrolled.value && val < SCROLL_EXIT) scrolled.value = false
}, { immediate: true })
</script>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 200;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border-light);
  transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

/* Elevated state: translucent frosted glass + layered shadow once scrolled. */
.top-nav--scrolled {
  background: color-mix(in srgb, var(--color-bg) 82%, transparent);
  border-bottom-color: transparent;
  box-shadow:
    0 1px 2px rgba(4, 26, 73, 0.06),
    0 8px 24px rgba(4, 26, 73, 0.08);
}

@supports (backdrop-filter: blur(12px)) or (-webkit-backdrop-filter: blur(12px)) {
  .top-nav--scrolled {
    background: color-mix(in srgb, var(--color-bg) 72%, transparent);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    backdrop-filter: saturate(180%) blur(12px);
  }
}

.top-nav__inner {
  display: flex;
  align-items: center;
  justify-content: center;
  /* Condenses slightly when scrolled for a tighter, more focused bar. */
  padding-top: var(--space-md);
  padding-bottom: var(--space-md);
  transition: padding 0.3s ease;
}

.top-nav--scrolled .top-nav__inner {
  padding-top: var(--space-sm);
  padding-bottom: var(--space-sm);
}

.top-nav__links {
  display: flex;
  justify-content: center;
  gap: var(--space-xl);
  list-style: none;
}

.top-nav__links a {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
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

.top-nav__links a:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 4px;
  border-radius: var(--radius-sm);
}

.top-nav__links a.router-link-exact-active {
  color: var(--color-primary);
  border-bottom-color: var(--color-accent);
}

/* Icons only show on mobile; the label carries desktop navigation. */
.top-nav__icon {
  display: none;
}

@media (max-width: 768px) {
  .top-nav__links {
    gap: var(--space-lg);
  }

  .top-nav__icon {
    display: block;
  }

  .top-nav__label {
    /* Mobile shows the suggestive icon only — keep the label for a11y. */
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .top-nav__links a {
    padding: var(--space-xs);
  }
}

@media (prefers-reduced-motion: reduce) {
  .top-nav,
  .top-nav__inner {
    transition: none;
  }
}
</style>
