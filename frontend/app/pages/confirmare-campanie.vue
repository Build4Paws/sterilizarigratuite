<template>
  <div class="container page-confirmare">
    <h1>Mulțumim!</h1>
    <p>Revenim în maxim 24 de ore cu confirmarea campaniei. Te anunțăm pe email când e aprobată.</p>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({
  robots: 'noindex, nofollow',
})
</script>

<style scoped>
.page-confirmare {
  padding: var(--space-2xl) 0;
  text-align: center;
}

.page-confirmare h1 {
  font-size: var(--font-size-xl);
  color: var(--color-success);
  margin-bottom: var(--space-md);
}
</style>
