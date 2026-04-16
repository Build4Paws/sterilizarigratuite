<template>
  <div :class="['ui-alert', `ui-alert--${variant}`]" role="alert">
    <component :is="icon" class="ui-alert__icon" :size="20" />
    <p class="ui-alert__message"><slot /></p>
  </div>
</template>

<script setup lang="ts">
import { CircleCheck, CircleAlert, Info } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  variant?: 'success' | 'error' | 'info'
}>(), {
  variant: 'info',
})

const icon = computed(() => {
  switch (props.variant) {
    case 'success': return CircleCheck
    case 'error': return CircleAlert
    default: return Info
  }
})
</script>

<style scoped>
.ui-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}

.ui-alert__icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.ui-alert--success {
  background: #ecfdf5;
  color: #065f46;
}

.ui-alert--error {
  background: #fef2f2;
  color: #991b1b;
}

.ui-alert--info {
  background: var(--color-slate-50);
  color: var(--color-primary);
}
</style>
