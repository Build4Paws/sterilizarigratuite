<template>
  <header class="top-nav" :class="{ 'top-nav--scrolled': scrolled, 'top-nav--menu-open': menuOpen }">
    <nav class="container top-nav__inner" aria-label="Navigare principală">
      <NuxtLink to="/" class="top-nav__logo" @click="menuOpen = false">
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

    <!-- Reading-progress indicator: grows as the page scrolls. Purely decorative. -->
    <div class="top-nav__progress" aria-hidden="true">
      <div class="top-nav__progress-bar" :style="{ transform: `scaleX(${progress})` }" />
    </div>
  </header>
</template>

<script setup lang="ts">
import { Menu, X } from 'lucide-vue-next'
import { useWindowScroll, useWindowSize, useEventListener } from '@vueuse/core'

const menuOpen = ref(false)

const links = [
  { to: '/', label: 'Acasă' },
  { to: '/campanii', label: 'Campanii' },
  { to: '/ghid-sterilizare', label: 'Ghid sterilizare' },
  { to: '/organizatori', label: 'Organizatori' },
  { to: '/harta', label: 'Harta' },
  { to: '/sustine', label: 'Doneaza' },
]

// Scroll state drives the condensed / elevated "frosted" header treatment.
const { y } = useWindowScroll()
const { width: winWidth, height: winHeight } = useWindowSize()

const SCROLL_ENTER = 64
const SCROLL_EXIT = 8
const scrolled = ref(false)
watch(y, (val) => {
  if (!scrolled.value && val > SCROLL_ENTER) scrolled.value = true
  else if (scrolled.value && val < SCROLL_EXIT) scrolled.value = false
}, { immediate: true })

// 0 → 1 reading progress for the accent bar along the header's bottom edge.
const progress = computed(() => {
  if (typeof document === 'undefined') return 0
  const max = document.documentElement.scrollHeight - winHeight.value
  if (max <= 0) return 0
  return Math.min(1, Math.max(0, y.value / max))
})

// Lock body scroll while the mobile menu is open so the backdrop feels anchored.
watch(menuOpen, (open) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = open ? 'hidden' : ''
})

// Close the mobile menu on Escape and when the viewport grows past the breakpoint.
useEventListener('keydown', (e: KeyboardEvent) => {
  if (e.key === 'Escape') menuOpen.value = false
})
watch(winWidth, (w) => {
  if (w > 768) menuOpen.value = false
})

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})
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
  justify-content: space-between;
  /* Condenses slightly when scrolled for a tighter, more focused bar. */
  padding-top: var(--space-md);
  padding-bottom: var(--space-md);
  transition: padding 0.3s ease;
}

.top-nav--scrolled .top-nav__inner {
  padding-top: var(--space-sm);
  padding-bottom: var(--space-sm);
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

.top-nav__logo-img {
  height: 36px;
  width: auto;
  transition: height 0.3s ease;
}

.top-nav--scrolled .top-nav__logo-img {
  height: 32px;
}

.top-nav__links {
  display: flex;
  gap: var(--space-xl);
  list-style: none;
}

.top-nav__links a {
  position: relative;
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

.top-nav__toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-xs);
  color: var(--color-text);
  border-radius: var(--radius-sm);
}

.top-nav__toggle:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* Reading-progress accent bar pinned to the header's bottom edge. */
.top-nav__progress {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  pointer-events: none;
}

.top-nav__progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-accent), var(--color-accent-hover));
  transform: scaleX(0);
  transform-origin: left center;
  /* Smooths the bar between scroll frames without lagging the scroll. */
  transition: transform 0.08s linear;
  will-change: transform;
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
    box-shadow: 0 12px 28px rgba(4, 26, 73, 0.12);
  }

  .top-nav__links--open {
    display: flex;
    animation: top-nav-drop 0.22s ease-out;
  }

  .top-nav__inner {
    position: relative;
  }

  @keyframes top-nav-drop {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}

@media (prefers-reduced-motion: reduce) {
  .top-nav,
  .top-nav__inner,
  .top-nav__logo-img,
  .top-nav__progress-bar {
    transition: none;
  }

  .top-nav__links--open {
    animation: none;
  }
}
</style>
