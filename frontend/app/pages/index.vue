<template>
  <div>
    <section class="hero">
      <div class="container">
        <h1>Sterilizare gratuită pentru câinele sau pisica ta</h1>
        <p class="hero__subtitle">
          Te anunțăm când se organizează o campanie de sterilizare gratuită în zona ta.
        </p>
        <!-- CitizenForm component will be added in Phase 3 -->
        <p class="hero__placeholder">[Formular înscriere cetățean — Phase 3]</p>
      </div>
    </section>

    <section class="bottom-band">
      <div class="container bottom-band__inner">
        <NuxtLink to="/campanii" class="bottom-band__link">
          Vezi campaniile active acum &rarr;
        </NuxtLink>
        <NuxtLink to="/organizatori" class="bottom-band__link">
          Ești ONG sau primărie? Anunță o campanie
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({
  title: 'Sterilizări Gratuite — Campanii de sterilizare pentru câini și pisici',
  description: 'Găsește campanii de sterilizare gratuită pentru câini și pisici în România. Înscrie-te și te anunțăm când apare o campanie în zona ta.',
  ogTitle: 'Sterilizări Gratuite',
  ogDescription: 'Te anunțăm când apare o campanie de sterilizare gratuită în zona ta.',
})
</script>

<style scoped>
.hero {
  padding: var(--space-2xl) 0;
  text-align: center;
}

.hero h1 {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  margin-bottom: var(--space-md);
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-muted);
  margin-bottom: var(--space-xl);
}

.hero__placeholder {
  padding: var(--space-xl);
  background: var(--color-bg-muted);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
}

.bottom-band {
  padding: var(--space-xl) 0;
  background: var(--color-bg-muted);
}

.bottom-band__inner {
  display: flex;
  justify-content: center;
  gap: var(--space-xl);
  flex-wrap: wrap;
}

.bottom-band__link {
  font-weight: 500;
}
</style>
