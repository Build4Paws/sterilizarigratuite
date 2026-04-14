<template>
  <div class="container page-confirmare">
    <h1>Ești înscris!</h1>
    <p>Te anunțăm când apare o campanie de sterilizare gratuită în zona ta.</p>
    <!-- Dynamic content (waiting count, clinics, magic link) added in Phase 2/3 -->
    <p class="placeholder">[Conținut dinamic confirmare — Phase 2/3]</p>
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

.placeholder {
  margin-top: var(--space-xl);
  padding: var(--space-xl);
  background: var(--color-bg-muted);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
}
</style>
