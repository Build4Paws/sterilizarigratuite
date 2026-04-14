<template>
  <div class="container page-campanii">
    <h1>Campanii de sterilizare gratuită</h1>
    <p class="page-campanii__intro">
      Toate campaniile de sterilizare gratuită aprobate, din toată România.
    </p>

    <!-- County filter + campaign list will be added in Phase 2/3 -->
    <p class="placeholder">[Filtru județ + listă campanii — Phase 2/3]</p>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({
  title: 'Campanii de sterilizare gratuită — Sterilizări Gratuite',
  description: 'Vezi toate campaniile de sterilizare gratuită pentru câini și pisici din România. Filtrează după județ și găsește campania cea mai apropiată.',
  ogTitle: 'Campanii de sterilizare gratuită',
  ogDescription: 'Găsește campanii de sterilizare gratuită pentru câini și pisici lângă tine.',
})
</script>

<style scoped>
.page-campanii {
  padding: var(--space-2xl) 0;
}

.page-campanii h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-sm);
}

.page-campanii__intro {
  color: var(--color-text-muted);
  margin-bottom: var(--space-xl);
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
