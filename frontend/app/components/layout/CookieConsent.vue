<template>
  <Transition name="cookie-slide">
    <aside
      v-if="!decided"
      class="cookie-consent"
      role="dialog"
      aria-live="polite"
      aria-label="Consimțământ pentru cookie-uri"
    >
      <div class="cookie-consent__inner">
        <p class="cookie-consent__text">
          Folosim cookie-uri pentru a înțelege cum este folosit site-ul și a-l
          îmbunătăți. Le activăm doar cu acordul tău. Detalii în
          <NuxtLink to="/politica-de-confidentialitate" class="cookie-consent__link">
            Politica de confidențialitate
          </NuxtLink>.
        </p>
        <div class="cookie-consent__actions">
          <UiButton variant="ghost" @click="decline">
            Refuz
          </UiButton>
          <UiButton variant="primary" @click="accept">
            Accept
          </UiButton>
        </div>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
const { decided, accept, decline } = useCookieConsent()
</script>

<style scoped>
.cookie-consent {
  position: fixed;
  bottom: var(--space-md);
  left: var(--space-md);
  right: var(--space-md);
  z-index: 100;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 30px rgba(4, 26, 73, 0.15);
  max-width: 640px;
  margin-inline: auto;
}

.cookie-consent__inner {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
}

.cookie-consent__text {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  line-height: 1.5;
}

.cookie-consent__link {
  color: var(--color-primary);
  text-decoration: underline;
}

.cookie-consent__actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
}

@media (min-width: 640px) {
  .cookie-consent__inner {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .cookie-consent__actions {
    flex-shrink: 0;
  }
}

/* Slide-up entrance; respects reduced-motion. */
.cookie-slide-enter-active,
.cookie-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.cookie-slide-enter-from,
.cookie-slide-leave-to {
  transform: translateY(1rem);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .cookie-slide-enter-active,
  .cookie-slide-leave-active {
    transition: none;
  }
}
</style>
