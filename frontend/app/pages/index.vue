<template>
  <div>
    <section class="hero">
      <div class="container hero__inner">
        <div class="hero__content">
          <h1 class="hero__title">
            Sterilizare gratuită pentru câinele sau pisica ta
          </h1>
          <p class="hero__subtitle">
            Te anunțăm când se organizează o campanie de sterilizare gratuită în zona ta.
          </p>
        </div>
        <div class="hero__form-wrapper">
          <FormsCitizenForm />
        </div>
      </div>
    </section>

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
.hero {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-3xl) 0;
}

.hero__inner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3xl);
  align-items: center;
}

.hero__title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-light);
  margin-bottom: var(--space-lg);
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-slate-300);
  font-weight: 400;
}

.hero__form-wrapper {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  color: var(--color-text);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.bottom-band {
  padding: var(--space-3xl) 0;
  background: var(--color-bg-muted);
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

@media (max-width: 768px) {
  .hero {
    padding: var(--space-2xl) 0;
  }

  .hero__inner {
    grid-template-columns: 1fr;
    gap: var(--space-xl);
  }

  .hero__title {
    font-size: var(--font-size-xl);
  }

  .hero__content {
    text-align: center;
  }

  .bottom-band__inner {
    grid-template-columns: 1fr;
  }
}
</style>
