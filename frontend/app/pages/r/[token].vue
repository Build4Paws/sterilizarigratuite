<template>
  <div class="container page-refresh">
    <h1>Mai ai animale de sterilizat?</h1>
    <!-- Refresh confirmation actions added in Phase 2/3 -->
    <p class="placeholder">[Da, ține-mă pe listă / Nu, dezabonează-mă — Phase 2/3]</p>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const _token = route.params.token

useSeoMeta({
  robots: 'noindex, nofollow',
})
</script>

<style scoped>
.page-refresh {
  padding: var(--space-2xl) 0;
  max-width: 500px;
  margin: 0 auto;
  text-align: center;
}

.page-refresh h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
}

.placeholder {
  padding: var(--space-xl);
  background: var(--color-bg-muted);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
}
</style>
