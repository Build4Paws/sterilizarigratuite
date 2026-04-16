<template>
  <div :class="['ui-field', { 'ui-field--error': error }]">
    <label :for="id" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>
    <select
      :id="id"
      :value="modelValue"
      :required="required"
      :disabled="disabled"
      :aria-invalid="!!error"
      :aria-describedby="error ? `${id}-error` : undefined"
      class="ui-field__select"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      @blur="$emit('blur')"
    >
      <option value="" disabled>{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
    <p v-if="error" :id="`${id}-error`" class="ui-field__error" role="alert">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
  label: string
  id: string
  placeholder?: string
  options: { value: string; label: string }[]
  required?: boolean
  disabled?: boolean
  error?: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()
</script>

<style scoped>
.ui-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.ui-field__label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
}

.ui-field__required {
  color: var(--color-error);
}

.ui-field__select {
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-input-bg);
  color: var(--color-text);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  padding-right: 2.5rem;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ui-field__select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}

.ui-field__select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-field--error .ui-field__select {
  border-color: var(--color-error);
}

.ui-field__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}
</style>
