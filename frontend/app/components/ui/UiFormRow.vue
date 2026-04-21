<template>
  <div class="form-row" :class="[`form-row--align-${align}`, { 'form-row--nowrap': nowrap }]">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  align?: 'start' | 'center' | 'end' | 'stretch'
  nowrap?: boolean
}>(), {
  align: 'stretch',
  nowrap: false,
})
</script>

<style scoped>
.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.form-row--nowrap {
  flex-wrap: nowrap;
}

.form-row--align-start { align-items: flex-start; }
.form-row--align-center { align-items: center; }
.form-row--align-end { align-items: flex-end; }
.form-row--align-stretch { align-items: stretch; }
</style>
