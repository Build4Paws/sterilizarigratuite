<template>
  <div class="home">
    <!-- Hero: navy background with centered title -->
    <section class="hero">
      <div class="container hero__inner">
        <h1 class="hero__title">
          Sterilizare gratuită pentru câinele sau pisica ta
        </h1>
        <p class="hero__subtitle">
          Te anunțăm când se organizează o campanie de sterilizare gratuită în localitatea ta.
        </p>
      </div>
    </section>

    <!-- Curved divider -->
    <div class="divider" aria-hidden="true">
      <svg viewBox="0 0 1440 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0,0 L0,60 Q360,120 720,80 Q1080,40 1440,90 L1440,0 Z" fill="var(--color-primary)" />
      </svg>
    </div>

    <!-- Form section: form overlaps into this area -->
    <section class="form-section">
      <div class="container form-section__inner">
        <div class="form-card">
          <FormsCitizenForm />
        </div>
      </div>
    </section>

    <!-- Bottom band -->
    <section class="bottom-band">
      <div class="container bottom-band__inner">
        <UiLinkCard
          to="/campanii"
          :icon="PawPrint"
          title="Campanii active"
          desc="Vezi campaniile de sterilizare gratuită din toată țara"
        />
        <UiLinkCard
          to="/despre-sterilizare"
          :icon="Stethoscope"
          title="Despre sterilizare"
          desc="Ghid medical — tot ce trebuie să știi înainte și după procedură"
        />
        <UiLinkCard
          to="/organizatori"
          :icon="Megaphone"
          title="Ești ONG sau primărie?"
          desc="Anunță o campanie de sterilizare și ajunge la cetățeni"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { PawPrint, Megaphone, Stethoscope } from 'lucide-vue-next'

useSeoMeta({
  title: 'Sterilizări Gratuite — Campanii de sterilizare pentru câini și pisici',
  description: 'Găsește campanii de sterilizare gratuită pentru câini și pisici în România. Înscrie-te și te anunțăm când apare o campanie în zona ta.',
  ogTitle: 'Sterilizări Gratuite — Build4Paws',
  ogDescription: 'Te anunțăm când apare o campanie de sterilizare gratuită în zona ta.',
})

useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: safeJsonLd({
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'Organization',
            name: 'Build4Paws',
            url: 'https://build4paws.ro',
            description: 'Tech NGO for animal welfare — building digital solutions for sterilization campaigns.',
          },
          {
            '@type': 'WebSite',
            name: 'Sterilizări Gratuite',
            url: 'https://sterilizarigratuite.ro',
            description: 'Platformă de sterilizare gratuită pentru câini și pisici în România.',
            publisher: {
              '@type': 'Organization',
              name: 'Build4Paws',
            },
          },
        ],
      }),
    },
  ],
})
</script>

<style scoped>
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
}

.hero__title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-light);
  margin-bottom: var(--space-md);
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-slate-300);
  font-weight: 400;
  max-width: 560px;
  margin: 0 auto;
}

/* Decorative illustrations */
.hero__decor {
  display: none;
  position: absolute;
  bottom: 2rem;
  z-index: 1;
  opacity: 0.8;
}

.hero__decor--left {
  left: 5%;
}

.hero__decor--right {
  right: 5%;
}

.hero__illustration {
  width: 140px;
  height: auto;
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
  max-width: 540px;
}

/* ---- Bottom band ---- */
.bottom-band {
  padding: var(--space-3xl) 0;
  background: var(--color-bg);
}

.bottom-band__inner {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
}


/* ---- Responsive ---- */
@media (min-width: 1300px) {
  .hero {
    padding: var(--space-3xl) 0 10rem;
  }

  .hero__title {
    font-size: var(--font-size-2xl);
  }

  .hero__decor {
    display: block;
  }

  .hero__illustration {
    width: 180px;
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

  .bottom-band__inner {
    grid-template-columns: 1fr;
    gap: var(--space-lg);
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .bottom-band__inner {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
