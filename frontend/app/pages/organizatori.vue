<template>
  <div class="page-organizatori">
    <!-- Hero -->
    <section class="hero">
      <div class="container hero__inner">
        <Megaphone class="hero__icon" :size="44" aria-hidden="true" />
        <h1 class="hero__title">Anunță o campanie de sterilizare</h1>
        <p class="hero__subtitle">
          Ești ONG sau primărie? Publică campania pe platformă și ajunge automat
          la cetățenii din zonă care așteaptă o campanie.
        </p>
      </div>
    </section>

    <!-- Curved divider -->
    <div class="divider" aria-hidden="true">
      <svg viewBox="0 0 1440 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0,0 L0,60 Q360,120 720,80 Q1080,40 1440,90 L1440,0 Z" fill="var(--color-primary)" />
      </svg>
    </div>

    <!-- Form section -->
    <section class="form-section">
      <div class="container form-section__inner">
        <div class="form-card">
          <FormsCampaignForm />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Megaphone } from 'lucide-vue-next'

useSeoMeta({
  title: 'Publică o campanie de sterilizare — Sterilizări Gratuite',
  description: 'Ești ONG sau primărie? Publică campania de sterilizare gratuită și ajunge automat la cetățenii din zonă care au animale de sterilizat.',
  ogTitle: 'Publică o campanie de sterilizare',
  ogDescription: 'Anunță campania ta de sterilizare gratuită — ajunge la cetățenii din zonă.',
})
</script>

<style scoped>
.page-organizatori {
  background: var(--color-bg-muted);
}

/* ---- Hero ---- */
.hero {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-3xl) 0 8rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero__inner {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
}

.hero__icon {
  color: var(--color-accent);
}

.hero__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-light);
  margin: 0;
  max-width: 700px;
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-slate-300);
  font-weight: 400;
  max-width: 560px;
  margin: 0 auto;
  line-height: 1.5;
}

/* ---- Curved divider ---- */
.divider {
  margin-top: -1px;
  line-height: 0;
  background: var(--color-bg-muted);
}

.divider svg {
  width: 100%;
  height: 80px;
  display: block;
}

/* ---- Form section ---- */
.form-section {
  background: var(--color-bg-muted);
  padding-bottom: var(--space-3xl);
}

.form-section__inner {
  display: flex;
  justify-content: center;
  margin-top: -6rem;
  position: relative;
  z-index: 3;
}

.form-card {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  color: var(--color-text);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  width: 100%;
  max-width: 720px;
}

/* ---- Responsive ---- */
@media (min-width: 1300px) {
  .hero {
    padding: var(--space-3xl) 0 10rem;
  }

  .hero__title {
    font-size: var(--font-size-2xl);
  }

  .form-section__inner {
    margin-top: -8rem;
  }
}

@media (max-width: 768px) {
  .hero {
    padding: var(--space-2xl) 0 6rem;
  }

  .hero__title {
    font-size: 1.75rem;
  }

  .hero__subtitle {
    font-size: 1.125rem;
  }

  .form-section__inner {
    margin-top: -4rem;
  }

  .form-card {
    padding: var(--space-lg);
  }

  .divider svg {
    height: 50px;
  }
}
</style>
