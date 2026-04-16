<template>
  <button
    :type="type"
    :class="['ui-btn', `ui-btn--${variant}`, { 'ui-btn--loading': loading }]"
    :disabled="disabled || loading"
  >
    <span v-if="loading" class="ui-btn__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost'
  type?: 'button' | 'submit' | 'reset'
  loading?: boolean
  disabled?: boolean
}>(), {
  variant: 'primary',
  type: 'button',
  loading: false,
  disabled: false,
})
</script>

<style scoped>
.ui-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.ui-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-btn--primary {
  background: var(--color-accent);
  color: var(--color-text-light);
  border-color: var(--color-accent);
}

.ui-btn--primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.ui-btn--secondary {
  background: var(--color-primary);
  color: var(--color-text-light);
  border-color: var(--color-primary);
}

.ui-btn--secondary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.ui-btn--ghost {
  background: transparent;
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.ui-btn--ghost:hover:not(:disabled) {
  background: var(--color-slate-50);
}

.ui-btn--loading {
  position: relative;
}

.ui-btn__spinner {
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
