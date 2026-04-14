<template>
  <div class="container page-organizatori">
    <h1>Anunță o campanie de sterilizare</h1>
    <p class="page-organizatori__intro">
      Ești ONG sau primărie și organizezi campanii de sterilizare gratuită?
      Publică campania pe platformă și ajunge automat la cetățenii din zonă.
    </p>

    <!-- CampaignForm component will be added in Phase 3 -->
    <p class="placeholder">[Formular publicare campanie — Phase 3]</p>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({
  title: 'Publică o campanie de sterilizare — Sterilizări Gratuite',
  description: 'Ești ONG sau primărie? Publică campania de sterilizare gratuită și ajunge automat la cetățenii din zonă care au animale de sterilizat.',
  ogTitle: 'Publică o campanie de sterilizare',
  ogDescription: 'Anunță campania ta de sterilizare gratuită — ajunge la cetățenii din zonă.',
})
</script>

<style scoped>
.page-organizatori {
  padding: var(--space-2xl) 0;
}

.page-organizatori h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-sm);
}

.page-organizatori__intro {
  color: var(--color-text-muted);
  margin-bottom: var(--space-xl);
  max-width: 600px;
}

.placeholder {
  padding: var(--space-xl);
  background: var(--color-bg-muted);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
