<template>
  <div :class="['ui-field', { 'ui-field--error': error }]">
    <label :for="id" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>
    <input
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :aria-invalid="!!error"
      :aria-describedby="error ? `${id}-error` : undefined"
      class="ui-field__input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @blur="$emit('blur')"
    />
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
  type?: string
  placeholder?: string
  required?: boolean
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

.ui-field__input {
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-input-bg);
  color: var(--color-text);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ui-field__input::placeholder {
  color: var(--color-slate-300);
}

.ui-field__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}

.ui-field--error .ui-field__input {
  border-color: var(--color-error);
}

.ui-field--error .ui-field__input:focus {
  box-shadow: 0 0 0 3px rgba(250, 45, 45, 0.1);
}

.ui-field__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}
</style>
