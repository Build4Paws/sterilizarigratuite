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
      :min="min"
      :max="max"
      :aria-invalid="!!error"
      :aria-describedby="describedBy"
      class="ui-field__input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @blur="$emit('blur')"
    />
    <p v-if="error" :id="`${id}-error`" class="ui-field__error" role="alert">
      {{ error }}
    </p>
    <p v-else-if="hint" :id="`${id}-hint`" class="ui-field__hint">
      {{ hint }}
    </p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue?: string
  label: string
  id: string
  type?: 'text' | 'email' | 'tel' | 'url' | 'number' | 'date' | 'time' | 'datetime-local' | 'password'
  placeholder?: string
  required?: boolean
  error?: string
  /** Helper text shown under the input when there is no error (e.g. expected date format). */
  hint?: string
  /** Forwarded to the input — useful for `date`/`time`/`number` constraints (e.g. min="2026-01-01"). */
  min?: string | number
  max?: string | number
}>()

defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const describedBy = computed(() => {
  if (props.error) return `${props.id}-error`
  if (props.hint) return `${props.id}-hint`
  return undefined
})
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

.ui-field__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* Native date/time pickers ship their own indicator and intrinsic sizing —
   normalize so they match other inputs in a row. */
.ui-field__input[type='date'],
.ui-field__input[type='time'],
.ui-field__input[type='datetime-local'] {
  font-family: var(--font-body);
  min-height: 2.625rem;
  appearance: none;
}

.ui-field__input[type='date']::-webkit-calendar-picker-indicator,
.ui-field__input[type='time']::-webkit-calendar-picker-indicator,
.ui-field__input[type='datetime-local']::-webkit-calendar-picker-indicator {
  cursor: pointer;
  opacity: 0.6;
}

.ui-field__input[type='date']::-webkit-calendar-picker-indicator:hover,
.ui-field__input[type='time']::-webkit-calendar-picker-indicator:hover,
.ui-field__input[type='datetime-local']::-webkit-calendar-picker-indicator:hover {
  opacity: 1;
}
</style>
