<template>
  <Transition name="back-to-top">
    <button
      v-show="visible"
      type="button"
      class="back-to-top"
      aria-label="Înapoi sus"
      @click="scrollToTop"
    >
      <ArrowUp :size="22" aria-hidden="true" />
    </button>
  </Transition>
</template>

<script setup lang="ts">
import { ArrowUp } from 'lucide-vue-next'
import { useWindowScroll } from '@vueuse/core'

// Show the button once the user has scrolled past ~600px.
const { y } = useWindowScroll()
const visible = computed(() => y.value > 600)

function scrollToTop() {
  const reduce = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' })
}
</script>

<style scoped>
.back-to-top {
  position: fixed;
  right: var(--space-lg);
  bottom: var(--space-lg);
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border: none;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-text-light);
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(4, 26, 73, 0.28);
  transition: background-color 0.2s ease, transform 0.15s ease;
}

.back-to-top:hover {
  background: var(--color-primary-hover);
}

.back-to-top:active {
  transform: scale(0.94);
}

.back-to-top:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* Fade + slide on appear/disappear. */
.back-to-top-enter-active,
.back-to-top-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.back-to-top-enter-from,
.back-to-top-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (prefers-reduced-motion: reduce) {
  .back-to-top-enter-active,
  .back-to-top-leave-active {
    transition: opacity 0.2s ease;
  }
  .back-to-top-enter-from,
  .back-to-top-leave-to {
    transform: none;
  }
}
</style>
