<template>
  <div class="page-sustine">
    <!-- Hero -->
    <section class="hero">
      <div class="container hero__inner">
        <Heart class="hero__icon" :size="44" aria-hidden="true" />
        <h1 class="hero__title">Cum ne poți sprijini</h1>
        <p class="hero__subtitle">
          Suntem o asociație non-profit care construiește unelte digitale pentru campaniile
          de sterilizare gratuită din România. Orice donație ne ajută să ținem platforma
          online și să ajungem la cât mai mulți oameni cu animale de sterilizat.
        </p>
      </div>
    </section>

    <!-- Curved divider -->
    <div class="divider" aria-hidden="true">
      <svg viewBox="0 0 1440 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0,0 L0,60 Q360,120 720,80 Q1080,40 1440,90 L1440,0 Z" fill="var(--color-primary)" />
      </svg>
    </div>

    <!-- Body -->
    <section class="body">
      <div class="container body__inner">

        <!-- Donation card -->
        <div class="card card--donate">
          <div class="card__header">
            <Landmark :size="22" class="card__header-icon" aria-hidden="true" />
            <h2 class="card__title">Donează prin transfer bancar</h2>
          </div>
          <p class="card__lead">
            Poți face o donație, unică sau recurentă, direct în contul asociației.
            Mulțumim din suflet pentru orice sprijin.
          </p>

          <dl class="details">
            <div class="details__row">
              <dt>Beneficiar</dt>
              <dd>Asociația Build 4 Paws</dd>
            </div>
            <div class="details__row details__row--iban">
              <dt>IBAN</dt>
              <dd>
                <code class="iban">{{ ibanDisplay }}</code>
                <button
                  type="button"
                  class="copy-btn"
                  :class="{ 'is-copied': copied }"
                  @click="copyIban"
                >
                  <component :is="copied ? Check : Copy" :size="16" aria-hidden="true" />
                  <span>{{ copied ? 'Copiat' : 'Copiază IBAN' }}</span>
                </button>
              </dd>
            </div>
            <div class="details__row">
              <dt>Bancă</dt>
              <dd>Banca Comercială Română (BCR)</dd>
            </div>
          </dl>
        </div>

        <!-- Legal details card -->
        <div class="card">
          <div class="card__header">
            <Building2 :size="22" class="card__header-icon" aria-hidden="true" />
            <h2 class="card__title">Date asociație</h2>
          </div>
          <p class="card__lead">
            Pentru colaborări oficiale sau confirmarea donației, acestea sunt datele noastre legale.
          </p>

          <dl class="details">
            <div class="details__row">
              <dt>Denumire</dt>
              <dd>Asociația Build 4 Paws</dd>
            </div>
            <div class="details__row">
              <dt>Formă juridică</dt>
              <dd>Asociație fără scop patrimonial (OG 26/2000)</dd>
            </div>
            <div class="details__row">
              <dt>Hotărâre</dt>
              <dd>Nr. 217/2026, 21.01.2026, Judecătoria Alba Iulia</dd>
            </div>
            <div class="details__row">
              <dt>CIF</dt>
              <dd>54236826</dd>
            </div>
            <div class="details__row">
              <dt>Email oficial</dt>
              <dd><a href="mailto:contact@build4paws.ro">contact@build4paws.ro</a></dd>
            </div>
          </dl>
        </div>

      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Heart, Landmark, Building2, Copy, Check } from 'lucide-vue-next'

// Canonical IBAN (no spaces) — what we copy to the clipboard.
const IBAN = 'RO55RNCB0068185806750001'
// Grouped in blocks of 4 for readability on screen.
const ibanDisplay = IBAN.replace(/(.{4})/g, '$1 ').trim()

const toast = useToast()
const copied = ref(false)

async function copyIban() {
  try {
    await navigator.clipboard.writeText(IBAN)
    copied.value = true
    toast.success('IBAN copiat. Mulțumim pentru sprijin!')
    setTimeout(() => { copied.value = false }, 2500)
  } catch {
    toast.error('Nu am putut copia IBAN-ul. Selectează-l și copiază-l manual.')
  }
}

useSeoMeta({
  title: 'Susține Build4Paws. Sterilizări gratuite pentru câini și pisici',
  description: 'Sprijină campaniile de sterilizare gratuită din România. Donează prin transfer bancar în contul Asociației Build 4 Paws.',
  ogTitle: 'Susține Build4Paws',
  ogDescription: 'Donația ta ajută campaniile de sterilizare gratuită să ajungă la cât mai mulți oameni.',
})
</script>

<style scoped>
.page-sustine {
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
  max-width: 620px;
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

/* ---- Body ---- */
.body {
  background: var(--color-bg-muted);
  padding-bottom: var(--space-3xl);
}

.body__inner {
  max-width: 720px;
  margin-top: -5rem;
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

/* ---- Cards ---- */
.card {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10), 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* Donation card gets an accent left edge to stand out as the primary action. */
.card--donate {
  border-left: 4px solid var(--color-accent);
}

.card__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.card__header-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}

.card__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  margin: 0;
  font-weight: 700;
}

.card__lead {
  color: var(--color-text-muted);
  line-height: 1.55;
  margin: 0;
}

/* ---- Detail rows ---- */
.details {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin: 0;
}

.details__row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-xs) var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px dashed var(--color-border-light);
}

.details__row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.details dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  min-width: 130px;
}

.details dd {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text);
  font-weight: 500;
}

.details dd a {
  color: var(--color-primary);
  font-weight: 500;
}

.details__row--iban dd {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
}

.iban {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 1.05rem;
  letter-spacing: 0.02em;
  color: var(--color-primary);
  background: var(--color-bg-muted);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

/* ---- Copy button ---- */
.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-light);
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-xs) var(--space-md);
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.copy-btn:hover {
  background: var(--color-accent-hover);
}

.copy-btn:active {
  transform: scale(0.97);
}

.copy-btn.is-copied {
  background: var(--color-success);
}

/* ---- Responsive ---- */
@media (min-width: 1300px) {
  .hero {
    padding: var(--space-3xl) 0 10rem;
  }

  .hero__title {
    font-size: var(--font-size-2xl);
  }

  .body__inner {
    margin-top: -7rem;
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

  .body__inner {
    margin-top: -3.5rem;
  }

  .card {
    padding: var(--space-lg);
  }

  .divider svg {
    height: 50px;
  }

  .details dt {
    min-width: 0;
  }

  .iban {
    font-size: 0.95rem;
  }
}
</style>
