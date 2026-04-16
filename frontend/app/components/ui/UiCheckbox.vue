<template>
  <div :class="['ui-checkbox', { 'ui-checkbox--error': error }]">
    <label :for="id" class="ui-checkbox__label">
      <input
        :id="id"
        type="checkbox"
        :checked="modelValue"
        :required="required"
        class="ui-checkbox__input"
        @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
      <span class="ui-checkbox__box" aria-hidden="true">
        <svg v-if="modelValue" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </span>
      <span class="ui-checkbox__text">
        <slot />
      </span>
    </label>
    <p v-if="error" class="ui-checkbox__error" role="alert">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean
  id: string
  required?: boolean
  error?: string
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<style scoped>
.ui-checkbox__label {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  cursor: pointer;
  font-size: var(--font-size-sm);
  line-height: 1.4;
}

.ui-checkbox__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.ui-checkbox__box {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s, border-color 0.15s;
  margin-top: 1px;
}

.ui-checkbox__box svg {
  width: 14px;
  height: 14px;
  color: var(--color-text-light);
}

.ui-checkbox__input:checked + .ui-checkbox__box {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.ui-checkbox__input:focus-visible + .ui-checkbox__box {
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.15);
}

.ui-checkbox__text {
  color: var(--color-text);
}

.ui-checkbox--error .ui-checkbox__box {
  border-color: var(--color-error);
}

.ui-checkbox__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  margin-top: var(--space-xs);
  padding-left: calc(20px + var(--space-sm));
}
</style>
