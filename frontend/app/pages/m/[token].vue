<template>
  <div class="container page-management">
    <h1>Gestionează înscrierea ta</h1>
    <!-- Token validation + actions added in Phase 2/3 -->
    <p class="placeholder">[Dezabonare / Ștergere GDPR — Phase 2/3]</p>
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
.page-management {
  padding: var(--space-2xl) 0;
  max-width: 500px;
  margin: 0 auto;
}

.page-management h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
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
