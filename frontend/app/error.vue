<template>
  <NuxtLayout>
    <section class="error-page">
      <div class="container error-page__inner">
        <p class="error-page__code">{{ statusCode }}</p>
        <h1 class="error-page__title">{{ title }}</h1>
        <p class="error-page__desc">{{ description }}</p>
        <div class="error-page__actions">
          <button type="button" class="error-page__cta" @click="goHome">
            Înapoi la pagina principală
          </button>
          <NuxtLink to="/campanii" class="error-page__link">Vezi campaniile →</NuxtLink>
        </div>
      </div>
    </section>
  </NuxtLayout>
</template>

<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const statusCode = computed(() => props.error?.statusCode ?? 404)
const is404 = computed(() => statusCode.value === 404)

const title = computed(() =>
  is404.value ? 'Pagina nu a fost găsită' : 'A apărut o eroare',
)

const description = computed(() =>
  is404.value
    ? 'Ne pare rău, pagina pe care o cauți nu există sau a fost mutată.'
    : 'Ne pare rău, ceva nu a funcționat. Încearcă din nou în câteva momente.',
)

useSeoMeta({
  title: () => `${statusCode.value} · ${title.value}`,
  robots: 'noindex, nofollow',
})

// `clearError` resets Nuxt's error state and navigates home in one step.
function goHome() {
  clearError({ redirect: '/' })
}
</script>

<style scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl) 0;
  min-height: 60vh;
}

.error-page__inner {
  text-align: center;
  max-width: 520px;
}

.error-page__code {
  font-family: var(--font-heading);
  font-size: var(--font-size-3xl);
  font-weight: 800;
  color: var(--color-accent);
  line-height: 1;
}

.error-page__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
  margin-top: var(--space-sm);
  line-height: 1.2;
}

.error-page__desc {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  line-height: 1.6;
  margin-top: var(--space-md);
}

.error-page__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  margin-top: var(--space-xl);
}

.error-page__cta {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: var(--font-size-base);
  color: var(--color-text-light);
  background: var(--color-accent);
  padding: var(--space-sm) var(--space-xl);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.error-page__cta:hover {
  background: var(--color-accent-hover);
}

.error-page__cta:active {
  transform: scale(0.98);
}

.error-page__link {
  color: var(--color-accent);
  font-weight: 600;
  font-size: var(--font-size-sm);
  text-decoration: none;
  transition: color 0.2s;
}

.error-page__link:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}
</style>
