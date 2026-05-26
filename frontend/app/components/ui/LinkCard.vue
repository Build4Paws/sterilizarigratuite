<template>
  <NuxtLink :to="to" class="link-card">
    <component :is="icon" class="link-card__icon" :size="28" aria-hidden="true" />
    <span class="link-card__title">{{ title }}</span>
    <span class="link-card__desc">{{ desc }}</span>
    <span class="link-card__arrow" aria-hidden="true">
      <ArrowRight :size="24" />
    </span>
  </NuxtLink>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { ArrowRight } from 'lucide-vue-next'

defineProps<{
  to: string
  title: string
  desc: string
  icon: Component
}>()
</script>

<style scoped>
.link-card {
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

.link-card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 12px rgba(249, 89, 5, 0.1);
  text-decoration: none;
}

.link-card__icon {
  color: var(--color-accent);
}

.link-card__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-primary);
}

.link-card__desc {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  flex: 1;
  line-height: 1.5;
}

.link-card__arrow {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-md);
  color: var(--color-accent);
  opacity: 0.6;
  transition: opacity 0.2s, transform 0.2s;
}

.link-card:hover .link-card__arrow {
  opacity: 1;
  transform: translateX(4px);
}
</style>
