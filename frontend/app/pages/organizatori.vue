<template>
  <div class="page-organizatori">
    <!-- Hero -->
    <section class="hero">
      <div class="container hero__inner">
        <Transition name="hero-swap" mode="out-in">
          <Megaphone v-if="formStep === 1" key="icon-form" class="hero__icon" :size="44" aria-hidden="true" />
          <Eye v-else key="icon-preview" class="hero__icon" :size="44" aria-hidden="true" />
        </Transition>
        <Transition name="hero-swap" mode="out-in">
          <h1 v-if="formStep === 1" key="title-form" class="hero__title">Anunță o campanie de sterilizare gratuită</h1>
          <h1 v-else key="title-preview" class="hero__title">Previzualizare campanie</h1>
        </Transition>
        <Transition name="hero-swap" mode="out-in">
          <p v-if="formStep === 1" key="sub-form" class="hero__subtitle">
            Durează 2 minute. În maxim 24 de ore aprobăm și notificăm prin SMS
            sau email toate persoanele înscrise din localitate.
          </p>
          <p v-else key="sub-preview" class="hero__subtitle">
            Așa va apărea campania ta pe pagina de campanii după aprobare.
            Verifică datele înainte să trimiți.
          </p>
        </Transition>
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
          <FormsCampaignForm @step-change="formStep = $event" />
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how">
      <div class="container">
        <h2 class="how__title">Cum ajungi la cetățeni în 3 pași</h2>
        <ol class="how__steps">
          <li v-for="(step, i) in steps" :key="i" class="how__step">
            <div class="how__step-num" aria-hidden="true">{{ i + 1 }}</div>
            <div class="how__step-icon-wrap" aria-hidden="true">
              <component :is="step.icon" :size="28" class="how__step-icon" />
            </div>
            <h3 class="how__step-title">{{ step.title }}</h3>
            <p class="how__step-text">{{ step.text }}</p>
          </li>
        </ol>
      </div>
    </section>

    <!-- FAQ -->
    <section class="faq">
      <div class="container faq__inner">
        <h2 class="faq__title">Întrebări frecvente</h2>
        <div class="faq__list">
          <details v-for="item in faqItems" :key="item.q" class="faq__item">
            <summary class="faq__question">
              <span>{{ item.q }}</span>
              <ChevronDown :size="20" class="faq__chevron" aria-hidden="true" />
            </summary>
            <div class="faq__answer" v-html="item.a" />
          </details>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  Megaphone,
  Eye,
  FilePlus2,
  ShieldCheck,
  Send,
  ChevronDown,
} from 'lucide-vue-next'

const formStep = ref<1 | 2>(1)

const steps = [
  {
    icon: FilePlus2,
    title: 'Completezi formularul',
    text: 'Când, unde și câte locuri ai. Durează doar 2 minute.',
  },
  {
    icon: ShieldCheck,
    title: 'Verificăm și aprobăm',
    text: 'În maxim 24 de ore primești confirmarea pe email.',
  },
  {
    icon: Send,
    title: 'Notificăm persoanele înscrise din localitate',
    text: 'Trimitem SMS sau email tuturor celor înscriși, fără niciun efort din partea ta.',
  },
]

const faqItems = [
  {
    q: 'Cine poate publica o campanie?',
    a: 'Orice ONG, primărie sau cabinet veterinar care organizează o campanie de sterilizare gratuită pentru câini și/sau pisici. Verificăm fiecare cerere înainte de publicare.',
  },
  {
    q: 'Costă ceva publicarea?',
    a: 'Nu. Publicarea pe platformă este gratuită. Scopul nostru este să ajutăm campaniile să ajungă la cât mai mulți cetățeni.',
  },
  {
    q: 'Cum sunt notificate persoanele înscrise?',
    a: 'Imediat ce campania ta este aprobată, trimitem automat SMS și email tuturor cetățenilor înregistrați din localitatea (și județul) tău. Tu nu trebuie să faci nimic.',
  },
  {
    q: 'Pot modifica o campanie după trimitere?',
    a: 'Pentru moment, modificările se fac prin email: răspunde la confirmarea pe care o primești de la noi cu schimbările dorite și actualizăm campania.',
  },
  {
    q: 'Ce date despre organizație sunt publice?',
    a: 'Publicăm doar numele organizației, locația, datele campaniei, numărul de locuri alocate campaniei, medicul (dacă îl specifici) și un telefon de contact pentru cetățeni. Emailul tău și telefonul de contact intern nu apar pe pagina publică.',
  },
]

useSeoMeta({
  title: 'Publică o campanie de sterilizare · Sterilizări Gratuite',
  description: 'Ești ONG sau primărie? Publică campania de sterilizare gratuită și ajunge automat la cetățenii din zonă care au animale de sterilizat.',
  ogTitle: 'Publică o campanie de sterilizare',
  ogDescription: 'Anunță campania ta de sterilizare gratuită și ajunge la cetățenii din zonă.',
})
</script>

<style scoped>
.page-organizatori {
  background: var(--color-bg-muted);
}

/* ---- Hero text swap transition ---- */
.hero-swap-enter-active,
.hero-swap-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.hero-swap-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.hero-swap-leave-to {
  opacity: 0;
  transform: translateY(-6px);
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
  padding-bottom: var(--space-2xl);
}

/* ---- How it works ---- */
.how {
  background: var(--color-bg-muted);
  padding: var(--space-2xl) 0 var(--space-3xl);
}

.how__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  text-align: center;
  margin: 0 0 calc(var(--space-xl) + var(--space-sm));
}

.how__steps {
  list-style: none;
  padding: var(--space-md) 0 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
}

.how__step {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: calc(var(--space-xl) + var(--space-xs)) var(--space-lg) var(--space-lg);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  position: relative;
  box-shadow: 0 4px 12px rgba(4, 26, 73, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.how__step:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(4, 26, 73, 0.10);
}

/* Floating numbered badge — orange disc with a soft ring matching the section
   background, so it reads as "punched out" of the card. */
.how__step-num {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-accent);
  color: var(--color-text-light);
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 1.15rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 18px rgba(249, 89, 5, 0.30),
    0 0 0 6px var(--color-bg-muted);
  letter-spacing: 0.01em;
}

.how__step:hover .how__step-num {
  box-shadow:
    0 10px 22px rgba(249, 89, 5, 0.38),
    0 0 0 6px var(--color-bg-muted);
}

.how__step-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: rgba(4, 26, 73, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: var(--space-sm) 0 var(--space-xs);
}

.how__step-icon {
  color: var(--color-primary);
}

.how__step-title {
  font-family: var(--font-heading);
  font-size: 1.1rem;
  color: var(--color-primary);
  margin: 0;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.how__step-text {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.55;
}

/* ---- FAQ ---- */
.faq {
  background: var(--color-bg);
  padding: var(--space-2xl) 0 var(--space-3xl);
}

.faq__inner {
  max-width: 720px;
}

.faq__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  text-align: center;
  margin: 0 0 var(--space-xl);
}

.faq__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.faq__item {
  background: var(--color-bg-muted);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light, #e2e8f0);
  overflow: hidden;
  transition: background-color 0.25s ease, border-color 0.25s ease;
}

.faq__item[open] {
  background: var(--color-bg);
  border-color: var(--color-primary);
}

.faq__question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
  list-style: none;
}

.faq__question::-webkit-details-marker {
  display: none;
}

.faq__chevron {
  color: var(--color-text-muted);
  flex-shrink: 0;
  transition: transform 0.25s ease;
}

.faq__item[open] .faq__chevron {
  transform: rotate(180deg);
}

.faq__answer {
  padding: 0 var(--space-lg) var(--space-md);
  color: var(--color-text);
  line-height: 1.6;
  font-size: var(--font-size-base);
}

/* Smooth open/close for <details>.
   Uses the new `::details-content` pseudo-element + `interpolate-size` so we
   can transition `block-size` to/from `auto`. Browsers without support
   (older Safari/Firefox) fall back to instant open — no broken layout. */
@supports (interpolate-size: allow-keywords) {
  :root {
    interpolate-size: allow-keywords;
  }

  .faq__item::details-content {
    block-size: 0;
    opacity: 0;
    overflow: clip;
    transition:
      block-size 0.3s ease,
      content-visibility 0.3s allow-discrete,
      opacity 0.25s ease;
  }

  .faq__item[open]::details-content {
    block-size: auto;
    opacity: 1;
  }
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

  .how__steps {
    grid-template-columns: 1fr;
    gap: var(--space-xl);
  }

  .faq__question {
    padding: var(--space-md);
    font-size: 0.95rem;
  }

  .faq__answer {
    padding: 0 var(--space-md) var(--space-md);
  }
}
</style>
