<template>
  <div class="container page-despre">
    <h1>Despre noi</h1>
    <p>
      Sterilizări Gratuite este un proiect <a href="https://build4paws.ro" target="_blank" rel="noopener">Build4Paws</a>
      care centralizează informația despre campaniile de sterilizare gratuită din România.
    </p>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({
  title: 'Despre noi — Sterilizări Gratuite',
  description: 'Sterilizări Gratuite este un proiect Build4Paws care centralizează campaniile de sterilizare gratuită din România.',
})
</script>

<style scoped>
.page-despre {
  padding: var(--space-2xl) 0;
  max-width: 700px;
}

.page-despre h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-md);
}
</style>
