<template>
  <div class="home">
    <!-- Hero: navy background with centered title -->
    <section class="hero">
      <div class="container hero__inner">
        <h1 class="hero__title">
          Sterilizare gratuită pentru câinele sau pisica ta
        </h1>
        <p class="hero__subtitle">
          Te anunțăm când se organizează o campanie de sterilizare gratuită în zona ta.
        </p>
      </div>

      <!-- Decorative illustrations — desktop only -->
      <div class="hero__decor hero__decor--left" aria-hidden="true">
        <svg viewBox="0 0 120 140" fill="none" xmlns="http://www.w3.org/2000/svg" class="hero__illustration">
          <!-- Dog silhouette -->
          <ellipse cx="60" cy="120" rx="40" ry="8" fill="rgba(255,255,255,0.06)" />
          <path d="M30 95 C30 75, 40 60, 60 55 C80 60, 90 75, 90 95 L90 110 C90 115, 85 118, 80 118 L40 118 C35 118, 30 115, 30 110 Z" fill="rgba(255,255,255,0.1)" />
          <circle cx="48" cy="80" r="3" fill="rgba(255,255,255,0.25)" />
          <circle cx="72" cy="80" r="3" fill="rgba(255,255,255,0.25)" />
          <ellipse cx="60" cy="88" rx="5" ry="3.5" fill="rgba(255,255,255,0.2)" />
          <path d="M28 68 C22 55, 25 42, 35 45 C40 47, 35 60, 33 68" fill="rgba(255,255,255,0.1)" />
          <path d="M92 68 C98 55, 95 42, 85 45 C80 47, 85 60, 87 68" fill="rgba(255,255,255,0.1)" />
          <path d="M50 105 L50 118" stroke="rgba(255,255,255,0.08)" stroke-width="3" stroke-linecap="round" />
          <path d="M70 105 L70 118" stroke="rgba(255,255,255,0.08)" stroke-width="3" stroke-linecap="round" />
          <path d="M90 95 C95 90, 105 92, 108 98 C110 102, 105 100, 100 97" fill="rgba(255,255,255,0.08)" />
        </svg>
      </div>
      <div class="hero__decor hero__decor--right" aria-hidden="true">
        <svg viewBox="0 0 120 130" fill="none" xmlns="http://www.w3.org/2000/svg" class="hero__illustration">
          <!-- Cat silhouette -->
          <ellipse cx="60" cy="115" rx="35" ry="6" fill="rgba(255,255,255,0.06)" />
          <path d="M35 90 C35 72, 45 60, 60 58 C75 60, 85 72, 85 90 L85 105 C85 110, 80 112, 75 112 L45 112 C40 112, 35 110, 35 105 Z" fill="rgba(255,255,255,0.1)" />
          <circle cx="50" cy="78" r="3.5" fill="rgba(255,255,255,0.25)" />
          <circle cx="70" cy="78" r="3.5" fill="rgba(255,255,255,0.25)" />
          <circle cx="50" cy="78" r="1.5" fill="rgba(255,255,255,0.15)" />
          <circle cx="70" cy="78" r="1.5" fill="rgba(255,255,255,0.15)" />
          <path d="M57 86 L60 88 L63 86" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M55 90 C52 92, 45 90, 40 88" stroke="rgba(255,255,255,0.1)" stroke-width="1" stroke-linecap="round" />
          <path d="M65 90 C68 92, 75 90, 80 88" stroke="rgba(255,255,255,0.1)" stroke-width="1" stroke-linecap="round" />
          <!-- Pointy ears -->
          <path d="M38 72 L28 48 L45 65" fill="rgba(255,255,255,0.1)" />
          <path d="M82 72 L92 48 L75 65" fill="rgba(255,255,255,0.1)" />
          <!-- Tail -->
          <path d="M85 100 C95 95, 105 85, 100 72 C98 67, 102 62, 108 60" stroke="rgba(255,255,255,0.1)" stroke-width="3" stroke-linecap="round" fill="none" />
        </svg>
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
        <NuxtLink to="/campanii" class="bottom-band__card">
          <PawPrint class="bottom-band__icon" :size="28" />
          <span class="bottom-band__card-title">Campanii active</span>
          <span class="bottom-band__card-desc">
            Vezi campaniile de sterilizare gratuită din toată țara &rarr;
          </span>
        </NuxtLink>
        <NuxtLink to="/organizatori" class="bottom-band__card">
          <Megaphone class="bottom-band__icon" :size="28" />
          <span class="bottom-band__card-title">Ești ONG sau primărie?</span>
          <span class="bottom-band__card-desc">
            Anunță o campanie de sterilizare și ajunge la cetățeni &rarr;
          </span>
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { PawPrint, Megaphone } from 'lucide-vue-next'

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
      innerHTML: JSON.stringify({
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
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xl);
}

.bottom-band__card {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-xl);
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  text-decoration: none;
  color: var(--color-text);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.bottom-band__card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 12px rgba(249, 89, 5, 0.1);
  text-decoration: none;
}

.bottom-band__icon {
  color: var(--color-accent);
}

.bottom-band__card-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-primary);
}

.bottom-band__card-desc {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
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
  }
}
</style>
